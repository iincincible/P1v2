import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    required_cols = ["odds_player_1", "odds_player_2"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    df["implied_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved odds features to {args.output_csv}")

if __name__ == "__main__":
    main()
