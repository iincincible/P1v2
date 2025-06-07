import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import glob
import os
import sys

# Allow utils import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import should_run, assert_file_exists
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_INITIAL_BANKROLL,
    DEFAULT_STRATEGY
)
from scripts.utils.filters import filter_value_bets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for value bet CSVs")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default=DEFAULT_STRATEGY)
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--odds_cap", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--initial_bankroll", type=float, default=DEFAULT_INITIAL_BANKROLL)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--save_plots", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError("❌ No value bet files found.")

    all_bets = []
    for file in files:
        try:
            assert_file_exists(file, "value_bets_csv")
            df = pd.read_csv(file)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
        except Exception as e:
            log_warning(f"Skipping {file} — normalization failed: {e}")
            continue

        if "winner" not in df.columns:
            if "actual_winner" in df.columns and "player_1" in df.columns:
                df["winner"] = (
                    df["actual_winner"].str.strip().str.lower() ==
                    df["player_1"].str.strip().str.lower()
                ).astype(int)
                log_info(f"Patched 'winner' column in: {file}")
            else:
                log_warning(f"Skipping {file} — cannot derive 'winner'")
                continue

        required_cols = {"expected_value", "odds", "predicted_prob", "winner"}
        if not required_cols.issubset(df.columns):
            log_warning(f"Skipping {file} — missing required columns after normalization.")
            continue

        # Use consistent filtering
        df = filter_value_bets(df, args.ev_threshold, args.odds_cap, max_margin=1.0)
        df["source_file"] = os.path.basename(file)
        all_bets.append(df)

    if not all_bets:
        raise ValueError("❌ No value bet files could be normalized or passed validation.")

    df = pd.concat(all_bets, ignore_index=True)
    df = df[df["expected_value"] <= 2.0]

    log_info(f"Loaded {len(df)} total bets from {len(files)} files")

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        initial_bankroll=args.initial_bankroll,
        ev_threshold=0.0,
        odds_cap=100.0,
        cap_fraction=0.05
    )

    sim_df.to_csv(args.output_csv, index=False)
    log_success(f"Saved simulation to {args.output_csv}")
    log_info(f"Final bankroll: {final_bankroll:.2f}")
    log_info(f"Max drawdown: {max_drawdown:.2f}")

    if args.plot or args.save_plots:
        png_path = os.path.splitext(args.output_csv)[0] + ".png"
        generate_bankroll_plot(sim_df["bankroll"], output_path=png_path if args.save_plots else None)

if __name__ == "__main__":
    main()
