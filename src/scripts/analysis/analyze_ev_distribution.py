import glob
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.logger import setup_logging, log_info, log_success, log_warning
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli_utils import cli_entrypoint


def analyze_ev_distribution(
    value_bets_files,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
) -> pd.DataFrame:
    """
    Analyze and return the EV distribution from value bet CSV files (pure function).
    """
    dfs = []
    for f in value_bets_files:
        try:
            df = pd.read_csv(f)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = df[(df["expected_value"] >= ev_threshold) & (df["odds"] <= max_odds)]
            dfs.append(df)
        except Exception as e:
            log_warning(f"Skipping {f}: {e}")
    if not dfs:
        raise ValueError("No valid value bet files after filtering.")
    all_bets = pd.concat(dfs, ignore_index=True)
    enforce_schema(all_bets, "value_bets")
    return all_bets


@cli_entrypoint
def main(
    value_bets_glob: str,
    output_csv: str = None,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    plot: bool = False,
    save_plot: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Analyze and plot the EV distribution from value bet CSV files.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = glob.glob(value_bets_glob)
    if not files:
        raise ValueError(f"No value bet files found matching: {value_bets_glob}")
    all_bets = analyze_ev_distribution(
        files, ev_threshold=ev_threshold, max_odds=max_odds
    )
    log_info(f"Loaded {len(all_bets)} filtered value bets across {len(files)} files.")

    if output_csv and not dry_run:
        all_bets.to_csv(output_csv, index=False)
        log_success(f"Saved filtered bets to {output_csv}")

    # Optionally plot
    if not all_bets.empty and (plot or save_plot):
        plt.figure(figsize=(10, 5))
        plt.hist(all_bets["expected_value"], bins=25, edgecolor="black")
        plt.title("EV Distribution (Filtered)")
        plt.xlabel("Expected Value")
        plt.ylabel("Number of Bets")
        plt.grid(True)

        if save_plot:
            if not output_csv:
                raise ValueError(
                    "--save_plot requires --output_csv to determine image path"
                )
            plot_path = Path(output_csv).with_name(
                Path(output_csv).stem + "_ev_distribution.png"
            )
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_path)
            log_success(f"Saved EV distribution plot to {plot_path}")

        if plot:
            plt.show()
