import argparse
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli_utils import (
    add_common_flags,
    assert_file_exists,
    output_file_guard,
)
from scripts.utils.logger import (
    log_error,
    log_info,
    log_success,
    log_warning,
)
from scripts.utils.normalize_columns import (
    normalize_columns,
    patch_winner_column,
)

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)


def get_git_commit():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        return commit
    except Exception:
        return None


@output_file_guard(output_arg="output_model")
def train_ev_filter_model(
    input_files,
    output_model,
    min_ev=0.2,
    overwrite=False,
    dry_run=False,
):
    output_path = Path(output_model)

    all_rows = []
    for path in input_files:
        try:
            assert_file_exists(path, "input_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = patch_winner_column(df)
            df = df[df["expected_value"] >= min_ev]
            if "winner" not in df.columns:
                log_warning(
                    f"⚠️ No 'winner' column in {path}, assigning synthetic labels."
                )
                df["winner"] = (df["expected_value"] > 0).astype(int)
            all_rows.append(df)
            log_info(f"✅ Loaded {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"❌ Failed to process {path}: {e}")

    if not all_rows:
        raise ValueError("❌ No valid input data found.")

    df = pd.concat(all_rows, ignore_index=True)
    log_success(f"📊 Training on {len(df)} rows with EV ≥ {min_ev}")

    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"]

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, test_size=0.25, random_state=42
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    log_info("📉 Evaluation on holdout set:")
    report = classification_report(y_test, model.predict(X_test), digits=3)
    log_info("\n" + report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    log_success(f"✅ Saved model to {output_path}")

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "model_type": "RandomForestClassifier",
        "features": features,
        "ev_threshold": min_ev,
        "train_rows": len(df),
        "input_files": input_files,
        "git_commit": get_git_commit(),
        "columns": list(df.columns),
        "train_preview": df.head(3).to_dict(orient="records"),
    }
    meta_path = output_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log_success(f"📄 Saved metadata to {meta_path}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Train EV filter model (RandomForest)."
    )
    parser.add_argument(
        "--input_files",
        nargs="+",
        required=True,
        help="CSV files with prediction features",
    )
    parser.add_argument(
        "--output_model", required=True, help="Path to save the trained model"
    )
    parser.add_argument(
        "--min_ev", type=float, default=0.2, help="Minimum EV threshold for training"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    train_ev_filter_model(
        input_files=_args.input_files,
        output_model=_args.output_model,
        min_ev=_args.min_ev,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )


if __name__ == "__main__":
    main()
