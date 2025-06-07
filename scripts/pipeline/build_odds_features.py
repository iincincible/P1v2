import pandas as pd
import argparse
from pathlib import Path
from scripts.utils.betting_math import compute_ev, compute_kelly_stake
from scripts.utils.cli_utils import should_run

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

    # Rename consistent odds columns
    df["odds_player_1"] = df["ltp_player_1"]
    df["odds_player_2"] = df["ltp_player_2"]

    # Compute implied probabilities and margin
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    df["implied_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    # Optional: compute EV using predicted_prob if already present
    if "predicted_prob" in df.columns:
        df["expected_value"] = compute_ev(df["predicted_prob"], df["odds_player_1"])
        df["kelly_stake"] = compute_kelly_stake(df["predicted_prob"], df["odds_player_1"])

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved odds features to {args.output_csv}")

if __name__ == "__main__":
    main()
