import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import glob
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_INITIAL_BANKROLL,
    DEFAULT_STRATEGY
)
from scripts.utils.filters import filter_value_bets


def main():
    parser = argparse.ArgumentParser(description="Simulate portfolio bankroll across value bet CSVs.")
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for value bet CSVs")
    parser.add_argument("--output_csv", required=True, help="Path to save simulation results")
    parser.add_argument("--strategy", choices=["flat", "kelly"], default=DEFAULT_STRATEGY)
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--odds_cap", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--initial_bankroll", type=float, default=DEFAULT_INITIAL_BANKROLL)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--save_plots", action="store_true")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
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
            df = patch_winner_column(df)
            df = add_ev_and_kelly(df)

            required = {"expected_value", "odds", "predicted_prob", "winner"}
            if not required.issubset(df.columns):
                log_warning(f"⚠️ Skipping {file} — missing required columns after normalization.")
                continue

            df = filter_value_bets(df, args.ev_threshold, args.odds_cap, max_margin=1.0)
            df["source_file"] = Path(file).name
            all_bets.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {file}: {e}")

    if not all_bets:
        raise ValueError("❌ No valid value bet files could be normalized or passed validation.")

    df = pd.concat(all_bets, ignore_index=True)
    df = df[df["expected_value"] <= 2.0]

    log_info(f"✅ Loaded {len(df)} total bets from {len(files)} files")

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        initial_bankroll=args.initial_bankroll,
        ev_threshold=0.0,
        odds_cap=100.0,
        cap_fraction=0.05
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sim_df.to_csv(output_path, index=False)
    log_success(f"✅ Saved simulation to {output_path}")
    log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
    log_info(f"📉 Max drawdown: {max_drawdown:.2f}")

    if args.plot or args.save_plots:
        png_path = output_path.with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=png_path if args.save_plots else None)


if __name__ == "__main__":
    main()
