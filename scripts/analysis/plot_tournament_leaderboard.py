import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import add_common_flags, should_run


def main():
    parser = argparse.ArgumentParser(description="Plot tournament leaderboard from summary CSV.")
    parser.add_argument("--input_csv", required=True, help="Path to tournament_leaderboard.csv")
    parser.add_argument("--output_png", default=None, help="Optional path to save PNG plot")
    parser.add_argument("--sort_by", choices=["roi", "profit", "total_bets"], default="roi")
    parser.add_argument("--top_n", type=int, default=20)
    parser.add_argument("--show", action="store_true", help="Show plot interactively")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_png) if args.output_png else None

    if output_path and not should_run(output_path, args.overwrite, args.dry_run):
        return

    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        log_warning(f"Failed to load CSV: {e}")
        return

    if args.sort_by not in df.columns:
        log_warning(f"Missing column to sort by: {args.sort_by}")
        return

    df = df.dropna(subset=[args.sort_by])
    df = df.sort_values(by=args.sort_by, ascending=False).head(args.top_n)

    plt.figure(figsize=(12, 6))
    bars = plt.barh(df["tournament"], df[args.sort_by], color="skyblue", edgecolor="black")
    plt.xlabel(args.sort_by.upper())
    plt.ylabel("Tournament")
    plt.title(f"Top {args.top_n} Tournaments by {args.sort_by.upper()}")
    plt.gca().invert_yaxis()
    plt.grid(True, axis='x')

    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height() / 2, f"{width:.2f}", va='center', ha='left')

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        log_success(f"🖼️ Saved leaderboard plot to {output_path}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
