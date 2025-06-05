import pandas as pd
import os
import glob
import argparse
import matplotlib.pyplot as plt
from tqdm import tqdm

def kelly_stake(prob, odds, bankroll):
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

        stake = 1.0 if strategy == "flat" else kelly_stake(prob, odds, bankroll)
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
            "ev": ev,
            "source_file": row.get("source_file", "unknown")
        })

    return pd.DataFrame(history), bankroll, max_drawdown

def load_valid_csvs():
    valid = []
    for f in glob.glob("data/processed/*_value_bets.csv"):
        if os.path.getsize(f) == 0:
            continue
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue

            # Force fallback mapping
            df["predicted_prob"] = df.get("pred_prob_player_1", df.get("predicted_prob"))
            df["odds"] = df.get("odds_player_1", df.get("odds"))
            df["expected_value"] = (df["predicted_prob"] * df["odds"]) - 1  # true EV

            if "winner" not in df.columns:
                if "actual_winner" in df.columns and "player_1" in df.columns and "player_2" in df.columns:
                    df["winner"] = df["actual_winner"].str.strip().str.lower() == df["player_1"].str.strip().str.lower()
                    df["winner"] = df["winner"].astype(int)
                else:
                    continue

            if df[["predicted_prob", "odds", "expected_value", "winner"]].dropna().empty:
                continue

            df["source_file"] = os.path.basename(f)
            valid.append(df)
        except Exception as e:
            print(f"⚠️ Skipped {f}: {e}")
            continue

    return pd.concat(valid, ignore_index=True) if valid else pd.DataFrame()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_csv", default="data/processed/bankroll_sim_all.csv")
    parser.add_argument("--strategy", choices=["flat", "kelly"], default="kelly")
    parser.add_argument("--ev_threshold", type=float, default=0.01)
    parser.add_argument("--odds_cap", type=float, default=10.0)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    df = load_valid_csvs()
    if df.empty:
        print("⚠️ No valid value bet files found.")
        return

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        ev_threshold=args.ev_threshold,
        odds_cap=args.odds_cap
    )

    if sim_df.empty:
        print("\n⚠️ No bets were executed after filtering. Nothing to plot or save.")
        return

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
