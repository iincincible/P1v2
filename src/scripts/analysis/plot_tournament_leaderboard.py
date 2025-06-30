from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from scripts.utils.logger import log_info, log_success, log_warning, setup_logging


def run_plot_leaderboard(
    df: pd.DataFrame,
    sort_by: str = "roi",
    top_n: int = 20,
):
    """
    Plot tournament leaderboard from summary DataFrame (pure function).
    """
    df = df.dropna(subset=[sort_by])
    df = df.sort_values(by=sort_by, ascending=False).head(top_n)
    if df.empty:
        log_warning("No data to plot after filtering.")
        return

    fig = plt.figure(figsize=(12, 6))
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

    # Return the figure so it can be managed by the CLI function
    return fig


def main_cli(args):
    """
    Wrapper function to be called from the main CLI entrypoint.
    """
    setup_logging(level="DEBUG" if args.verbose else "INFO", json_logs=args.json_logs)

    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    df = pd.read_csv(input_csv)
    log_info(f"Loaded {len(df)} rows from {input_csv}")

    fig = run_plot_leaderboard(df, sort_by=args.sort_by, top_n=args.top_n)

    if fig:
        if args.output_png and not args.dry_run:
            plt.savefig(args.output_png)
            log_success(f"Saved leaderboard plot to {args.output_png}")
        if args.show:
            plt.show()

        plt.close(fig)  # Ensure figure is closed to free memory
