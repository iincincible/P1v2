# File: src/scripts/modeling/train_ev_filter_model.py

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.cli_utils import (
    add_common_flags,
    assert_file_exists,
    output_file_guard,
)
from scripts.utils.logger import log_error, log_info, log_success
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column

logging.basicConfig(level=logging.INFO)


@output_file_guard(output_arg="output_model")
def train_ev_filter_model(
    input_files, output_model, min_ev=0.2, overwrite=False, dry_run=False
):
    all_rows = []

    for path in input_files:
        try:
            assert_file_exists(path, "input_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = patch_winner_column(df)
            df = df[df["expected_value"] >= min_ev]
            all_rows.append(df)
            log_info(f"✅ Loaded {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"❌ Skipping {path}: {e}")

    if not all_rows:
        raise ValueError("❌ No valid input data found after filtering.")

    df = pd.concat(all_rows, ignore_index=True)
    log_success(f"📊 Training on {len(df)} rows with EV ≥ {min_ev}")

    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"]
    groups = df["match_id"] if "match_id" in df.columns else None

    # Use GroupShuffleSplit to avoid data leakage between train/test
    if groups is not None:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    else:
        raise ValueError("❌ 'match_id' column required for grouped splitting")

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    log_info("📉 Evaluation on holdout set:")
    report = classification_report(y_test, model.predict(X_test), digits=3)
    log_info("\n" + report)

    output_path = Path(output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    log_success(f"✅ Saved model to {output_model}")

    meta = {
        "timestamp": datetime.now().isoformat(),
        "model_type": "RandomForestClassifier",
        "features": features,
        "ev_threshold": min_ev,
        "train_rows": len(df),
        "input_files": input_files,
        "columns": list(df.columns),
    }
    with open(output_path.with_suffix(".json"), "w") as f:
        json.dump(meta, f, indent=2)
    log_success(f"📄 Saved metadata to {output_path.with_suffix('.json')}")


def main():
    parser = argparse.ArgumentParser(description="Train EV filter model (RFC).")
    parser.add_argument("--input_files", nargs="+", required=True)
    parser.add_argument("--output_model", required=True)
    parser.add_argument("--min_ev", type=float, default=0.2)
    add_common_flags(parser)
    args = parser.parse_args()
    train_ev_filter_model(
        input_files=args.input_files,
        output_model=args.output_model,
        min_ev=args.min_ev,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
