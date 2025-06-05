import argparse
import pandas as pd
import joblib
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    df = pd.read_csv(args.input_csv)
    model = joblib.load(args.model_path)

    features = ["implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff"]
    df["predicted_prob"] = model.predict_proba(df[features])[:, 1]

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

if __name__ == "__main__":
    main()
