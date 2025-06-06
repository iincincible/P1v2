import sys
sys.path.append(r"C:\Users\lucap\Projects\P1v2\.venv\Lib\site-packages")  # 🩹 Hack to force joblib import

import argparse
import pandas as pd
import joblib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)

    # 🛠 Patch missing implied_prob_diff if needed
    if "implied_prob_diff" not in df.columns and "implied_prob_1" in df.columns and "implied_prob_2" in df.columns:
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    model = joblib.load(args.model_path)

    X = df[["implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"]]
    preds = model.predict_proba(X)

    df["pred_prob_player_1"] = preds[:, 1]
    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

if __name__ == "__main__":
    main()
