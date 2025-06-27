import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import (
    setup_logging,
    log_info,
    log_success,
    log_warning,
)


def plot_leaderboard(
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


@cli_entrypoint
def main(
    input_csv: str,
    output_png: str = None,
    sort_by: str = "roi",
    top_n: int = 20,
    show: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Plot tournament leaderboard from summary CSV.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    df = pd.read_csv(input_csv)
    log_info(f"Loaded {len(df)} rows from {input_csv}")

    plot_leaderboard(df, sort_by=sort_by, top_n=top_n)

    if output_png and not dry_run:
        plt.savefig(output_png)
        log_success(f"Saved leaderboard plot to {output_png}")
    if show:
        plt.show()
