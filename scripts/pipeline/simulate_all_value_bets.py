# scripts/pipeline/simulate_all_value_bets.py

import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import glob
import os
import sys

# Allow importing utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns


def simulate_bankroll(df, strategy, initial_bankroll):
    bankroll = initial_bankroll
    peak = bankroll
    max_drawdown = 0
    bankroll_trajectory = [bankroll]
    logs = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Simulating bankroll"):
        stake = 1.0 if strategy == "flat" else min(bankroll, bankroll * row["kelly_stake"])
        win = row["winner"]
        odds = row["odds"]
        payout = stake * (odds - 1) if win else -stake
        bankroll += payout
        peak = max(peak, bankroll)
        max_drawdown = max(max_drawdown, peak - bankroll)
        bankroll_trajectory.append(bankroll)

        logs.append({
            "match": row.get("match_id", ""),
            "stake": stake,
            "odds": odds,
            "won": bool(win),
            "payout": payout,
            "bankroll": bankroll
        })

    return bankroll, max_drawdown, bankroll_trajectory, pd.DataFrame(logs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for value bet CSVs")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default="kelly")
    parser.add_argument("--ev_threshold", type=float, default=0.2)
    parser.add_argument("--odds_cap", type=float, default=6.0)
    parser.add_argument("--initial_bankroll", type=float, default=1000.0)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--save_plots", action="store_true")
    args = parser.parse_args()

    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError("❌ No valid value bet files found.")

    all_bets = []
    for file in files:
        try:
            df = pd.read_csv(file)
            df = normalize_columns(df)
        except Exception as e:
            print(f"⚠️ Skipping {file} — normalization failed: {e}")
            continue

        # Patch 'winner' if missing
        if "winner" not in df.columns:
            if "actual_winner" in df.columns and "player_1" in df.columns:
                df["winner"] = (
                    df["actual_winner"].str.strip().str.lower() ==
                    df["player_1"].str.strip().str.lower()
                ).astype(int)
                print(f"🩹 Patched 'winner' column in: {file}")
            else:
                print(f"⚠️ Skipping {file} — cannot derive 'winner'")
                continue

        required_cols = {"expected_value", "odds", "predicted_prob", "winner"}
        if not required_cols.issubset(df.columns):
            print(f"⚠️ Skipping {file} — missing required columns after normalization.")
            continue

        df["source_file"] = os.path.basename(file)
        all_bets.append(df)

    if not all_bets:
        raise ValueError("❌ No value bet files could be normalized or passed validation.")

    df = pd.concat(all_bets, ignore_index=True)
    print(f"📊 Loaded {len(df)} total bets from {len(files)} files")

    # Apply filters
    df = df[df["expected_value"] >= args.ev_threshold]
    df = df[df["odds"] <= args.odds_cap]
    print(f"✅ {len(df)} bets after applying EV ≥ {args.ev_threshold} and odds ≤ {args.odds_cap}")

    # Compute Kelly stake if needed
    if args.strategy == "kelly":
        df["kelly_stake"] = (df["predicted_prob"] - (1 / df["odds"])) / (1 - (1 / df["odds"]))
        df["kelly_stake"] = df["kelly_stake"].clip(lower=0)

    final_bankroll, max_drawdown, trajectory, logs = simulate_bankroll(df, args.strategy, args.initial_bankroll)
    df["strategy"] = args.strategy
    df["stake"] = logs["stake"]
    df["payout"] = logs["payout"]
    df["final_bankroll"] = final_bankroll
    df["max_drawdown"] = max_drawdown

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved simulation to {args.output_csv}")
    print(f"💰 Final bankroll: {final_bankroll:,.2f}")
    print(f"📉 Max drawdown: {max_drawdown:,.2f}")

    if args.plot or args.save_plots:
        plt.figure(figsize=(10, 5))
        plt.plot(trajectory)
        plt.title("Bankroll Trajectory")
        plt.xlabel("Bet Number")
        plt.ylabel("Bankroll")
        if args.save_plots:
            out_path = os.path.splitext(args.output_csv)[0] + ".png"
            plt.savefig(out_path)
            print(f"🖼️ Saved bankroll plot to {out_path}")
        if args.plot:
            plt.show()


if __name__ == "__main__":
    main()
