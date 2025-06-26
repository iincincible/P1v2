import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.cli import guarded_run
from scripts.utils.logger import setup_logging, log_info, log_success, log_error
from scripts.utils.normalize_columns import (
    normalize_and_patch_canonical_columns,
    patch_winner_column,
    enforce_canonical_columns,
)


@guarded_run
def main(
    input_files: str,  # Space-separated list of files (string from CLI)
    output_model: str,
    min_ev: float = 0.2,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Train a RandomForest EV filter model on CSVs with canonical columns.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = input_files.split()
    all_rows = []
    for path in files:
        try:
            df = pd.read_csv(path)
            df = normalize_and_patch_canonical_columns(df, context=path)
            df = patch_winner_column(df)
            df = df[df["expected_value"] >= min_ev]
            all_rows.append(df)
            log_info(f"Loaded {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"Skipping {path}: {e}")

    if not all_rows:
        raise ValueError("No valid input data found after filtering.")

    df = pd.concat(all_rows, ignore_index=True)
    enforce_canonical_columns(df, context="train_ev_filter_model")
    log_success(f"Training on {len(df)} rows with EV ≥ {min_ev}")

    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"]
    if "match_id" in df.columns:
        groups = df["match_id"]
    else:
        raise ValueError("'match_id' column required for grouped splitting")

    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    log_info("Evaluation on holdout set:")
    report = classification_report(y_test, model.predict(X_test), digits=3)
    log_info("\n" + report)

    output_path = Path(output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        joblib.dump(model, output_path)
        log_success(f"Saved model to {output_model}")

        meta = {
            "timestamp": datetime.now().isoformat(),
            "model_type": "RandomForestClassifier",
            "features": features,
            "ev_threshold": min_ev,
            "train_rows": len(df),
            "input_files": files,
            "columns": list(df.columns),
        }
        with open(output_path.with_suffix(".json"), "w") as f:
            json.dump(meta, f, indent=2)
        log_success(f"Saved metadata to {output_path.with_suffix('.json')}")


if __name__ == "__main__":
    main()
