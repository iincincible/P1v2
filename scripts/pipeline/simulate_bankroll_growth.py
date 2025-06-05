import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

def kelly_stake(prob, odds, bankroll):
    """Return the Kelly bet size."""
    b = odds - 1
    q = 1 - prob
    edge = (b * prob - q) / b
    return max(0, edge * bankroll)

def simulate_bankroll(df, strategy="flat", starting_bankroll=1000, ev_threshold=0.01, odds_cap=10.0):
    bankroll = starting_bankroll
    max_drawdown = 0
    peak = bankroll
    history = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Simulating bankroll"):
        prob = row["predicted_prob"]
        odds = row["odds"]
        ev = row["expected_value"]
        won = row["winner"]

        if pd.isna(prob) or pd.isna(odds) or pd.isna(ev):
            continue
        if ev < ev_threshold or odds > odds_cap:
            continue

        if strategy == "flat":
            stake = 1.0
        elif strategy == "kelly":
            stake = kelly_stake(prob, odds, bankroll)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csvs", required=True, help="Comma-separated list of CSV files")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.01)
    parser.add_argument("--odds_cap", type=float, default=10.0)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default="flat")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    # 🔧 Split comma-separated list
    files = args.input_csvs.split(",")

    # Load and tag each file
    df = pd.concat(
        [pd.read_csv(f).assign(source_file=os.path.basename(f)) for f in files],
        ignore_index=True
    )

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        ev_threshold=args.ev_threshold,
        odds_cap=args.odds_cap
    )

    sim_df.to_csv(args.output_csv, index=False)

    print(f"\n📈 Simulated {len(sim_df)} bets")
    print(f"💰 Final bankroll: {final_bankroll:.2f}")
    print(f"📉 Max drawdown: {max_drawdown:.2f}")

    if args.plot:
        plt.plot(sim_df["bankroll"])
        plt.title("Bankroll Over Time")
        plt.xlabel("Bet Number")
        plt.ylabel("Bankroll")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
