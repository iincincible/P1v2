import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

def kelly_stake(prob, odds, bankroll):
    b = odds - 1
    q = 1 - prob
    edge = (b * prob - q) / b if b > 0 else 0
    stake = edge * bankroll
    return max(0, min(stake, bankroll * 0.05))

def simulate_bankroll(df, strategy="flat", starting_bankroll=1000, ev_threshold=0.01, odds_cap=10.0):
    bankroll = starting_bankroll
    max_drawdown = 0
    peak = bankroll
    history = []

    actual_strategy = strategy
    if strategy == "kelly" and len(df) < 10:
        print(f"⚠️ Only {len(df)} bets — switching to flat staking for safety.")
        actual_strategy = "flat"

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Simulating bankroll"):
        prob = row["predicted_prob"]
        odds = row["odds"]
        ev = row["expected_value"]
        won = row["winner"]

        if pd.isna(prob) or pd.isna(odds) or pd.isna(ev):
            continue
        if ev < ev_threshold or odds > odds_cap:
            continue

        stake = 1.0 if actual_strategy == "flat" else kelly_stake(prob, odds, bankroll)
        payout = stake * (odds if won else 0)
        bankroll += payout - stake
        peak = max(peak, bankroll)
        drawdown = peak - bankroll
        max_drawdown = max(max_drawdown, drawdown)

        history.append({
            "bankroll": bankroll,
            "stake": stake,
            "payout": payout,
            "odds": odds,
            "won": won,
            "ev": ev
        })

    return pd.DataFrame(history), bankroll, max_drawdown

def save_plot(df, png_path):
    if "bankroll" not in df.columns or df.empty:
        print("⚠️ No bankroll data to plot — skipping plot generation.")
        return
    plt.figure(figsize=(10, 5))
    plt.plot(df["bankroll"])
    plt.xlabel("Bet #")
    plt.ylabel("Bankroll")
    plt.title("Simulated Bankroll Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(png_path)
    print(f"🖼️ Saved bankroll plot to {png_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csvs", required=True, help="Comma-separated list of CSV files")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.01)
    parser.add_argument("--odds_cap", type=float, default=10.0)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default="flat")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    files = args.input_csvs.split(",")
    df = pd.concat([pd.read_csv(f).assign(source_file=os.path.basename(f)) for f in files], ignore_index=True)

    # Patch missing columns
    if "predicted_prob" not in df.columns:
        df["predicted_prob"] = df.get("pred_prob_player_1", pd.NA)
    if "odds" not in df.columns:
        df["odds"] = df.get("odds_player_1", pd.NA)
    if "expected_value" not in df.columns:
        df["expected_value"] = (df["predicted_prob"] * df["odds"]) - 1
    if "winner" not in df.columns:
        if "actual_winner" in df.columns and "player_1" in df.columns:
            df["winner"] = df["actual_winner"].str.strip().str.lower() == df["player_1"].str.strip().str.lower()
            df["winner"] = df["winner"].astype(int)
        else:
            raise ValueError("❌ 'winner' column missing and cannot be derived from actual_winner/player_1")

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df, strategy=args.strategy, ev_threshold=args.ev_threshold, odds_cap=args.odds_cap
    )

    sim_df.to_csv(args.output_csv, index=False)
    print(f"\n📈 Simulated {len(sim_df)} bets")
    print(f"💰 Final bankroll: {final_bankroll:.2f}")
    print(f"📉 Max drawdown: {max_drawdown:.2f}")

    png_path = os.path.splitext(args.output_csv)[0] + ".png"
    save_plot(sim_df, png_path)

    if args.plot:
        plt.show()

if __name__ == "__main__":
    main()
