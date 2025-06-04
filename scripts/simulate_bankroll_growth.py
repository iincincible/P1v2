import argparse
import pandas as pd
from tqdm import tqdm
import os

def simulate(df, strategy="kelly", fixed_stake=10.0):
    bankroll = 1000.0
    max_drawdown = 0.0
    peak = bankroll
    bankroll_history = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Simulating bankroll"):
        prob = row["predicted_prob"]
        odds = row["odds"]
        winner = row["winner"]

        # Skip obviously broken rows
        if pd.isna(prob) or pd.isna(odds):
            continue

        # Kelly stake (fraction of bankroll)
        if strategy == "kelly":
            edge = prob * (odds - 1) - (1 - prob)
            frac = edge / (odds - 1) if odds > 1 else 0
            stake = max(0, frac) * bankroll
        else:
            stake = fixed_stake

        payout = stake * (odds if winner else -1)
        bankroll += payout
        peak = max(peak, bankroll)
        drawdown = peak - bankroll
        max_drawdown = max(max_drawdown, drawdown)

        bankroll_history.append({
            "bet": row.get("player", row.get("player_1", "UNKNOWN")),
            "stake": stake,
            "odds": odds,
            "prob": prob,
            "won": winner,
            "bankroll": bankroll
        })

    return pd.DataFrame(bankroll_history), bankroll, max_drawdown

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csvs", nargs="+", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot_path", default=None)
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    parser.add_argument("--odds_cap", type=float, default=100.0)
    parser.add_argument("--strategy", choices=["kelly", "fixed"], default="kelly")
    parser.add_argument("--fixed_stake", type=float, default=10.0)
    args = parser.parse_args()

    # Load value bet CSV(s)
    files = args.input_csvs
    df = pd.concat([pd.read_csv(f).assign(source_file=os.path.basename(f)) for f in files], ignore_index=True)

    # Detect long format
    if {"player", "predicted_prob", "odds", "expected_value", "winner"}.issubset(df.columns):
        long_format = True
    else:
        raise ValueError("Missing expected long-format columns in input CSV.")

    # Filter high-EV, capped-odds bets
    df = df[df["expected_value"] > args.ev_threshold]
    df = df[df["odds"] <= args.odds_cap]

    # Simulate
    history, final_bankroll, max_drawdown = simulate(df, strategy=args.strategy, fixed_stake=args.fixed_stake)

    # Output
    history.to_csv(args.output_csv, index=False)
    print(f"\n📈 Simulated {len(history)} bets")
    print(f"💰 Final bankroll: {final_bankroll:.2f}")
    print(f"📉 Max drawdown: {max_drawdown:.2f}")

if __name__ == "__main__":
    main()
