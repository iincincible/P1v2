import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils.cli import guarded_run
from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    setup_logging,
)


@guarded_run
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
    Plot tournament leaderboard from summary CSV.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    try:
        df = pd.read_csv(input_csv)
        log_info(f"Loaded {len(df)} rows from {input_csv}")
    except Exception as e:
        log_error(f"Failed to read {input_csv}: {e}")
        raise

    if sort_by not in df.columns:
        log_error(f"Missing column to sort by: {sort_by}")
        raise ValueError(f"Missing sort column: {sort_by}")

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

    if output_png:
        plt.savefig(output_png)
        log_success(f"Saved leaderboard plot to {output_png}")

    if show:
        plt.show()


if __name__ == "__main__":
    main()
