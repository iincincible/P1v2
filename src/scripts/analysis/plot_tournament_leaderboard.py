import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists


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

    # Dry-run: log actions but do nothing
    if _args.dry_run:
        log_dryrun(
            f"Would load leaderboard from {_args.input_csv}, "
            f"sort by {_args.sort_by}, take top {_args.top_n}"
        )
        if _args.output_png:
            log_dryrun(f"Would save plot to {_args.output_png}")
        return

    input_path = Path(_args.input_csv)
    assert_file_exists(input_path, "input_csv")

    try:
        df = pd.read_csv(input_path)
        log_info(f"📥 Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        log_error(f"❌ Failed to read {input_path}: {e}")
        return

    if _args.sort_by not in df.columns:
        log_error(f"❌ Missing column to sort by: {_args.sort_by}")
        return

    df = df.dropna(subset=[_args.sort_by])
    df = df.sort_values(by=_args.sort_by, ascending=False).head(_args.top_n)

    if df.empty:
        log_warning("⚠️ No data to plot after filtering.")
        return

    plt.figure(figsize=(12, 6))
    bars = plt.barh(df["tournament"], df[_args.sort_by], edgecolor="black")
    plt.xlabel(_args.sort_by.upper())
    plt.ylabel("Tournament")
    plt.title(f"Top {_args.top_n} Tournaments by {_args.sort_by.upper()}")
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

    if _args.output_png:
        output_path = Path(_args.output_png)
        if should_run(output_path, _args.overwrite, _args.dry_run):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path)
            log_success(f"🖼️ Saved leaderboard plot to {output_path}")

    if _args.show:
        plt.show()


if __name__ == "__main__":
    main()
