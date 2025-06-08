import argparse
import pandas as pd
import joblib
import json
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags
from scripts.utils.constants import DEFAULT_EV_THRESHOLD


def main():
    parser = argparse.ArgumentParser(description="Train EV filter model (RandomForest).")
    parser.add_argument("--input_files", nargs="+", required=True, help="CSV files with prediction features")
    parser.add_argument("--output_model", required=True, help="Path to save the trained model")
    parser.add_argument("--min_ev", type=float, default=DEFAULT_EV_THRESHOLD, help="Minimum EV threshold for training")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_model)
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    all_rows = []
    for path in args.input_files:
        try:
            assert_file_exists(path, "input_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = patch_winner_column(df)
            df = df[df["expected_value"] >= args.min_ev]
            if "winner" not in df.columns:
                log_warning(f"⚠️ No 'winner' column in {path}, assigning synthetic labels.")
                df["winner"] = (df["expected_value"] > 0).astype(int)
            all_rows.append(df)
            log_info(f"✅ Loaded {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"❌ Failed to process {path}: {e}")

    if not all_rows:
        raise ValueError("❌ No valid input data found.")

    df = pd.concat(all_rows, ignore_index=True)
    log_success(f"📊 Training on {len(df)} rows with EV ≥ {args.min_ev}")

    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.25, random_state=42)
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
        "ev_threshold": args.min_ev,
        "train_rows": len(df),
        "input_files": args.input_files
    }
    meta_path = output_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log_success(f"📄 Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
