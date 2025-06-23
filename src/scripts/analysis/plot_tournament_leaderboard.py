import argparse
import pandas as pd
import matplotlib.pyplot as plt
import logging
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, output_file_guard, assert_file_exists

# Refactor: Add logging config
logging.basicConfig(level=logging.INFO)

@output_file_guard(output_arg="output_png")
def plot_tournament_leaderboard(
    input_csv,
    output_png=None,
    sort_by="roi",
    top_n=20,
    show=False,
    overwrite=False,
    dry_run=False,
):
    assert_file_exists(input_csv, "input_csv")

    try:
        df = pd.read_csv(input_csv)
        log_info(f"📥 Loaded {len(df)} rows from {input_csv}")
    except Exception as e:
        log_error(f"❌ Failed to read {input_csv}: {e}")
        return

    if sort_by not in df.columns:
        log_error(f"❌ Missing column to sort by: {sort_by}")
        return

    df = df.dropna(subset=[sort_by])
    df = df.sort_values(by=sort_by, ascending=False).head(top_n)

    if df.empty:
        log_warning("⚠️ No data to plot after filtering.")
        return

    plt.figure(figsize=(12, 6))
    bars = plt.barh(df["tournament"], df[sort_by], edgecolor="black")
    plt.xlabel(sort_by.upper())
    plt.ylabel("Tournament")
    plt.title(f"Top {top_n} Tournaments by {sort_by.upper()}")
    plt.gca().invert_yaxis()
    plt.grid(True, axis="x")

    for bar in bars:
        width = bar.get_width()
        plt.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.2f}",
            va="center",
            ha="left",
        )

    plt.tight_layout()

    if output_png:
        plt.savefig(output_png)
        log_success(f"🖼️ Saved leaderboard plot to {output_png}")

    if show:
        plt.show()

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Plot tournament leaderboard from summary CSV."
    )
    parser.add_argument(
        "--input_csv", required=True, help="Path to tournament_leaderboard.csv"
    )
    parser.add_argument(
        "--output_png", default=None, help="Optional path to save PNG plot"
    )
    parser.add_argument(
        "--sort_by",
        choices=["roi", "profit", "total_bets"],
        default="roi",
        help="Column to sort by",
    )
    parser.add_argument(
        "--top_n", type=int, default=20, help="Number of top rows to display"
    )
    parser.add_argument("--show", action="store_true", help="Show plot interactively")
    add_common_flags(parser)
    _args = parser.parse_args(args)
    plot_tournament_leaderboard(
        input_csv=_args.input_csv,
        output_png=_args.output_png,
        sort_by=_args.sort_by,
        top_n=_args.top_n,
        show=_args.show,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
