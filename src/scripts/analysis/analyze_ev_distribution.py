import glob
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.logger import setup_logging, log_info, log_success, log_warning
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS
from scripts.utils.betting_math import add_ev_and_kelly


def run_analyze_ev_distribution(
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


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze EV distribution from value bet CSV files."
    )
    parser.add_argument("--value_bets_glob", required=True)
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
    setup_logging(level="DEBUG" if args.verbose else "INFO", json_logs=args.json_logs)
    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError(f"No value bet files found matching: {args.value_bets_glob}")
    all_bets = run_analyze_ev_distribution(
        files, ev_threshold=args.ev_threshold, max_odds=args.max_odds
    )
    log_info(f"Loaded {len(all_bets)} filtered value bets across {len(files)} files.")

    if args.output_csv and not args.dry_run:
        all_bets.to_csv(args.output_csv, index=False)
        log_success(f"Saved filtered bets to {args.output_csv}")

    # Optionally plot
    if not all_bets.empty and (args.plot or args.save_plot):
        plt.figure(figsize=(10, 5))
        plt.hist(all_bets["expected_value"], bins=25, edgecolor="black")
        plt.title("EV Distribution (Filtered)")
        plt.xlabel("Expected Value")
        plt.ylabel("Number of Bets")
        plt.grid(True)

        if args.save_plot:
            if not args.output_csv:
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


if __name__ == "__main__":
    main_cli()
