import pandas as pd
import argparse
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli_utils import should_run
from scripts.utils.normalize_columns import normalize_columns

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    df = pd.read_csv(args.input_csv)

    # Rename and standardize columns
    df["odds_player_1"] = df["ltp_player_1"]
    df["odds_player_2"] = df["ltp_player_2"]

    # Compute implied probabilities and margin
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    # Normalize + optionally compute EV/Kelly if predicted_prob exists
    df = normalize_columns(df)
    if "predicted_prob" in df.columns:
        df = add_ev_and_kelly(df)

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved odds features to {args.output_csv}")

if __name__ == "__main__":
    main()
