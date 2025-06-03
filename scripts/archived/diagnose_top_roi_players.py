# scripts/diagnose_top_roi_players.py

import pandas as pd
import argparse
import matplotlib.pyplot as plt
import os

def load_and_plot(input_csv, min_bets=20, top_n=10, output_plot=None):
    df = pd.read_csv(input_csv)

    # Filter to players with at least min_bets
    df = df[df["num_bets"] >= min_bets]

    # Sort by ROI descending
    top_players = df.sort_values("roi", ascending=False).head(top_n)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.barh(top_players["player"], top_players["roi"], color="skyblue")
    plt.xlabel("ROI")
    plt.title(f"Top {top_n} ROI Players (min {min_bets} bets)")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    if output_plot:
        plt.savefig(output_plot)
        print(f"✅ Saved ROI plot to {output_plot}")
    else:
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Path to player ROI CSV")
    parser.add_argument("--min_bets", type=int, default=20, help="Minimum number of bets to include a player")
    parser.add_argument("--top_n", type=int, default=10, help="Number of top players to show")
    parser.add_argument("--output_plot", help="Optional output path for saving plot")
    args = parser.parse_args()

    load_and_plot(
        input_csv=args.input_csv,
        min_bets=args.min_bets,
        top_n=args.top_n,
        output_plot=args.output_plot
    )
