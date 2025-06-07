import argparse
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from pathlib import Path

from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import should_run

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for *_value_bets.csv")
    parser.add_argument("--ev_threshold", type=float, default=0.2)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--output_csv", type=str, default=None)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--save_plot", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError("No value bet files found.")

    # Early output skip (if filtered CSV or plot already exists)
    if args.output_csv and not should_run(args.output_csv, args.overwrite, args.dry_run):
        return
    if args.save_plot and args.output_csv:
        out_plot_path = Path(args.output_csv).with_name(Path(args.output_csv).stem + "_ev_distribution.png")
        if not should_run(out_plot_path, args.overwrite, args.dry_run):
            return

    dfs = []
    for file in files:
        df = pd.read_csv(file)
        df = normalize_columns(df)
        df = df[df["expected_value"] >= args.ev_threshold]
        df = df[df["odds"] <= args.max_odds]
        dfs.append(df)

    all_bets = pd.concat(dfs, ignore_index=True)
    log_info(f"Loaded {len(all_bets)} value bets after filtering")

    if args.output_csv:
        all_bets.to_csv(args.output_csv, index=False)
        log_success(f"Saved filtered bets to {args.output_csv}")

    # Plot EV histogram
    plt.figure(figsize=(10, 5))
    plt.hist(all_bets["expected_value"], bins=25, color="blue", edgecolor="black")
    plt.title("EV Distribution (Filtered)")
    plt.xlabel("Expected Value")
    plt.ylabel("Number of Bets")
    plt.grid(True)

    if args.save_plot:
        out_path = (
            Path(args.output_csv).with_name(Path(args.output_csv).stem + "_ev_distribution.png")
            if args.output_csv else "ev_distribution.png"
        )
        plt.savefig(out_path)
        log_success(f"Saved EV distribution plot to {out_path}")

    if args.plot:
        plt.show()

if __name__ == "__main__":
    main()
