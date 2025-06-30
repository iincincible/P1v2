import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS
from scripts.utils.decorators import with_logging
from scripts.utils.file_utils import load_dataframes
from scripts.utils.logger import log_info, log_success
from scripts.utils.schema import enforce_schema, normalize_columns


def run_analyze_ev_distribution(
    df: pd.DataFrame,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
) -> pd.DataFrame:
    """
    Analyze and return the EV distribution from a DataFrame of value bets (pure function).
    """
    df = normalize_columns(df)
    df = add_ev_and_kelly(df)
    df_filtered = df[
        (df["expected_value"] >= ev_threshold) & (df["odds"] <= max_odds)
    ].copy()
    if df_filtered.empty:
        raise ValueError("No valid value bet files after filtering.")

    enforce_schema(df_filtered, "value_bets")
    return df_filtered


@with_logging
def main_cli():
    parser = argparse.ArgumentParser(
        description="Analyze EV distribution from value bet CSV files."
    )
    parser.add_argument(
        "--value_bets_glob",
        required=True,
        help="Glob pattern for input value bet CSV files (e.g., 'data/*_value_bets.csv').",
    )
    parser.add_argument("--output_csv", default=None)
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--save_plot", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()

    all_bets_raw = load_dataframes(args.value_bets_glob)

    all_bets = run_analyze_ev_distribution(
        all_bets_raw, ev_threshold=args.ev_threshold, max_odds=args.max_odds
    )
    log_info(f"Loaded and filtered {len(all_bets)} value bets.")

    if args.output_csv and not args.dry_run:
        all_bets.to_csv(args.output_csv, index=False)
        log_success(f"Saved filtered bets to {args.output_csv}")

    # Optionally plot
    if not all_bets.empty and (args.plot or args.save_plot):
        fig = plt.figure(figsize=(10, 5))
        plt.hist(all_bets["expected_value"], bins=25, edgecolor="black")
        plt.title("EV Distribution (Filtered)")
        plt.xlabel("Expected Value")
        plt.ylabel("Number of Bets")
        plt.grid(True)

        if args.save_plot:
            if not args.output_csv:
                plt.close(fig)
                raise ValueError(
                    "--save_plot requires --output_csv to determine image path"
                )
            plot_path = Path(args.output_csv).with_name(
                Path(args.output_csv).stem + "_ev_distribution.png"
            )
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_path)
            log_success(f"Saved EV distribution plot to {plot_path}")

        if args.plot:
            plt.show()

        plt.close(fig)  # Ensure figure is closed to free memory


if __name__ == "__main__":
    main_cli()
