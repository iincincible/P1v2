import argparse
import pandas as pd
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from datetime import datetime

from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.filters import filter_value_bets
from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags


def main():
    parser = argparse.ArgumentParser(description="Train EV filter model (RandomForest).")
    parser.add_argument("--input_files", nargs="+", required=True, help="CSV files with prediction features")
    parser.add_argument("--output_model", required=True, help="Path to save the trained model")
    parser.add_argument("--min_ev", type=float, default=0.2, help="Minimum EV threshold for training")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_model)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    rows = []
    for file in args.input_files:
        try:
            assert_file_exists(file, "input_csv")
            df = pd.read_csv(file)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = patch_winner_column(df)
            df = df[df["expected_value"] >= args.min_ev]

            if "winner" not in df.columns:
                log_warning(f"⚠️ No 'winner' column in {file}, using synthetic label.")
                df["winner"] = (df["expected_value"] > 0).astype(int)

            rows.append(df)
            log_info(f"✅ Loaded {len(df)} rows from {file}")
        except Exception as e:
            log_error(f"❌ Failed to load {file}: {e}")

    if not rows:
        raise ValueError("❌ All input files failed to load or were empty.")

    df = pd.concat(rows, ignore_index=True)
    log_success(f"📊 Training on {len(df)} rows (EV ≥ {args.min_ev})")

    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.25, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    log_info("📉 Classification report (holdout set):")
    report = classification_report(y_test, model.predict(X_test), digits=3, output_dict=True)
    log_info("\n" + classification_report(y_test, model.predict(X_test), digits=3))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    log_success(f"✅ Saved EV filter model to {output_path}")

    # === Metadata logging ===
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "features": features,
        "train_rows": len(df),
        "ev_threshold": args.min_ev,
        "input_files": args.input_files,
        "accuracy": report.get("accuracy"),
        "precision": report.get("1", {}).get("precision"),
        "recall": report.get("1", {}).get("recall"),
        "f1_score": report.get("1", {}).get("f1-score"),
    }
    meta_path = output_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log_success(f"📄 Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
