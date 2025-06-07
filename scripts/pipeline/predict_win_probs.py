import argparse
import pandas as pd
import joblib
import os
import sys

# Patch import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.cli_utils import should_run

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

    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)

    model = joblib.load(args.model_path)
    X = df[model.feature_names_in_]
    preds = model.predict_proba(X)

    df["pred_prob_player_1"] = preds[:, 1]
    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

if __name__ == "__main__":
    main()
