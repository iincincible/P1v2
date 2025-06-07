import argparse
import pandas as pd
import joblib
import os
import sys

# Patch import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.cli_utils import should_run, assert_file_exists
from scripts.utils.logger import log_info, log_success, log_error

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.input_csv, "input_csv")
    assert_file_exists(args.model_path, "model_path")

    log_info(f"📥 Loading input: {args.input_csv}")
    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)

    log_info(f"📦 Loading model: {args.model_path}")
    model = joblib.load(args.model_path)

    required_features = list(model.feature_names_in_)
    missing = [f for f in required_features if f not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing model features in input: {missing}")

    X = df[required_features]
    preds = model.predict_proba(X)

    df["pred_prob_player_1"] = preds[:, 1]
    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]

    # Fallback assignment for confidence_score
    if "confidence_score" not in df.columns:
        df["confidence_score"] = df["pred_prob_player_1"]
        log_info("🔧 Set confidence_score = pred_prob_player_1")

    log_info(f"✅ Generated predictions for {len(df)} rows")
    log_info(f"📊 Mean pred_prob_player_1: {df['pred_prob_player_1'].mean():.4f}")

    df.to_csv(args.output_csv, index=False)
    log_success(f"✅ Saved predictions to {args.output_csv}")

if __name__ == "__main__":
    main()
