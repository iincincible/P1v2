# File: src/scripts/pipeline/predict_win_probs.py

import argparse
import pandas as pd
import joblib
import logging
from pathlib import Path

from scripts.utils.normalize_columns import (
    CANONICAL_REQUIRED_COLUMNS,
    normalize_and_patch_canonical_columns,
    enforce_canonical_columns,
)

logging.basicConfig(level=logging.INFO)


def predict_win_probs(
    model_file, input_csv, output_csv, overwrite=False, dry_run=False
):
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logging.info(f"[SKIP] {output_csv} exists and --overwrite not set")
        return

    # Load model
    try:
        model = joblib.load(model_file)
        logging.info(f"📥 Loaded model from {model_file}")
    except Exception as e:
        logging.error(f"❌ Could not load model: {e}")
        return

    # Load data
    df = pd.read_csv(input_csv)
    logging.info(f"📥 Loaded {len(df)} rows from {input_csv}")

    # Features the model expects
    features = getattr(
        model,
        "feature_names_in_",
        ["implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"],
    )
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        logging.warning(
            f"⚠️ Model expects features missing in input: {missing_features}. Filling with NaN."
        )
        for f in missing_features:
            df[f] = float("nan")

    # Drop rows with NaNs in model features
    initial_len = len(df)
    df = df.dropna(subset=features)
    logging.info(
        f"Dropped {initial_len - len(df)} rows with NaN in model features before prediction. Remaining: {len(df)} rows."
    )
    if len(df) == 0:
        logging.error("No rows left after dropping NaNs in model features. Exiting.")
        # But still write out empty canonical columns for downstream
        empty_df = pd.DataFrame(columns=CANONICAL_REQUIRED_COLUMNS)
        empty_df.to_csv(output_csv, index=False)
        return

    # Predict win probabilities
    try:
        if hasattr(model, "predict_proba"):
            df["predicted_prob"] = model.predict_proba(df[features])[:, 1]
        else:
            df["predicted_prob"] = model.predict(df[features])
        logging.info("✅ Added predicted_prob column.")
    except Exception as e:
        logging.error(f"Failed during prediction: {e}")
        # Still patch output
        df["predicted_prob"] = float("nan")

    # Always patch/normalize all canonical columns for downstream
    df = normalize_and_patch_canonical_columns(df, context="predict_win_probs")

    # Output, ensuring canonical columns
    try:
        enforce_canonical_columns(df, context="predict_win_probs_output")
    except Exception as e:
        logging.warning(f"⚠️ Output missing canonical columns after patch: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"✅ Saved predictions to {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Predict win probabilities using trained model."
    )
    parser.add_argument("--model_file", required=True)
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    predict_win_probs(
        model_file=args.model_file,
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
