import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds_csv", required=True)
    parser.add_argument("--save_csv", required=True)
    parser.add_argument("--save_plot", required=True)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--bin_size", type=float, default=0.05)
    args = parser.parse_args()

    df = pd.read_csv(args.preds_csv)
    if "expected_value" not in df.columns or "odds" not in df.columns or "winner" not in df.columns:
        raise ValueError("❌ Required columns missing: expected_value, odds, winner")

    df = df[df["odds"] <= args.max_odds].copy()
    df["ev_bin"] = (df["expected_value"] // args.bin_size) * args.bin_size

    # Simulate flat stake ROI
    df["payout"] = df["winner"] * (df["odds"] - 1)
    grouped = df.groupby("ev_bin").agg(
        n_bets=("winner", "count"),
        win_rate=("winner", "mean"),
        avg_odds=("odds", "mean"),
        avg_ev=("expected_value", "mean"),
        roi=("payout", "mean")  # net return per $1 staked
    ).reset_index()

    # Save and plot
    Path(args.save_csv).parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(args.save_csv, index=False)

    plt.figure(figsize=(10, 5))
    plt.plot(grouped["ev_bin"], grouped["roi"], marker="o", label="ROI (flat staking)")
    plt.axhline(0, color="gray", linestyle="--")
    plt.xlabel("EV bin")
    plt.ylabel("ROI per $1 staked")
    plt.title("ROI by Expected Value Bin")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.save_plot)
    print(f"✅ Saved CSV to {args.save_csv}")
    print(f"📈 Saved plot to {args.save_plot}")

if __name__ == "__main__":
    main()
