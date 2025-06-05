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
    model = joblib.load(args.model_path)

    X = df[["odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff"]]
    df["pred_prob_player_1"] = model.predict_proba(X)[:, 1].clip(0.05, 0.95)

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

if __name__ == "__main__":
    main()
