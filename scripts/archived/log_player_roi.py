import argparse
import pandas as pd
import glob
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=True, help="Path to simulated bankroll CSV(s)")
    parser.add_argument("--output_csv", required=True, help="Where to save the player ROI summary")
    args = parser.parse_args()

    files = glob.glob(args.input_glob)
    if not files:
        raise FileNotFoundError(f"No files found for pattern: {args.input_glob}")

    df_list = [pd.read_csv(f) for f in files]
    bets_df = pd.concat(df_list, ignore_index=True)

    if bets_df.empty:
        print("⚠️ No bets found in input files.")
        return

    if "player_staked" not in bets_df.columns or "stake" not in bets_df.columns or "player_payout" not in bets_df.columns:
        raise ValueError("Missing one of the required columns: 'player_staked', 'stake', or 'player_payout'.")

    summary = bets_df.groupby("player_staked").agg(
        num_bets=("stake", "count"),
        total_staked=("stake", "sum"),
        total_payout=("player_payout", "sum")
    ).reset_index().rename(columns={"player_staked": "player"})

    summary["roi"] = (summary["total_payout"] - summary["total_staked"]) / summary["total_staked"]
    summary = summary.sort_values(by="roi", ascending=False)

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    print(f"✅ Saved player ROI log to {args.output_csv}")


if __name__ == "__main__":
    main()
