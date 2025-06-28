import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.logger import setup_logging, log_info, log_success, log_warning


def run_plot_leaderboard(
    df: pd.DataFrame,
    sort_by: str = "roi",
    top_n: int = 20,
) -> None:
    """
    Plot tournament leaderboard from summary DataFrame (pure function).
    """
    df = df.dropna(subset=[sort_by])
    df = df.sort_values(by=sort_by, ascending=False).head(top_n)
    if df.empty:
        log_warning("No data to plot after filtering.")
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


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot tournament leaderboard from summary CSV."
    )
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_png", default=None)
    parser.add_argument("--sort_by", default="roi")
    parser.add_argument("--top_n", type=int, default=20)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    setup_logging(level="DEBUG" if args.verbose else "INFO", json_logs=args.json_logs)
    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    df = pd.read_csv(input_csv)
    log_info(f"Loaded {len(df)} rows from {input_csv}")

    run_plot_leaderboard(df, sort_by=args.sort_by, top_n=args.top_n)

    if args.output_png and not args.dry_run:
        plt.savefig(args.output_png)
        log_success(f"Saved leaderboard plot to {args.output_png}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main_cli()
