import argparse
import pandas as pd
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def predict_win_probs(
    model_file, input_csv, output_csv, overwrite=False, dry_run=False
):
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logging.info(f"[SKIP] {output_csv} exists and --overwrite not set")
        return

    # Load model
    model = joblib.load(model_file)
    logging.info(f"📥 Loaded model from {model_file}")

    # Load data
    df = pd.read_csv(input_csv)
    logging.info(f"📥 Loaded {len(df)} rows from {input_csv}")

    # Define features expected by the model
    features = ["implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"]

    # Drop rows with any NaNs in model features
    initial_len = len(df)
    df = df.dropna(subset=features)
    logging.info(
        f"Dropped {initial_len - len(df)} rows with NaN in model features before prediction. Remaining: {len(df)} rows."
    )

    if len(df) == 0:
        logging.error("No rows left after dropping NaNs in model features. Exiting.")
        return

    # Predict win probabilities
    try:
        df["predicted_prob"] = model.predict_proba(df[features])[:, 1]
        logging.info("✅ Added predicted_prob column.")
    except Exception as e:
        logging.error(f"Failed during prediction: {e}")
        return

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
