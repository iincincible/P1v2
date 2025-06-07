import argparse
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS, DEFAULT_STRATEGY
from scripts.utils.filters import filter_value_bets


def main():
    parser = argparse.ArgumentParser(description="Simulate bankroll growth from one or more value bet files.")
    parser.add_argument("--input_csvs", required=True, help="Comma-separated list of value bet CSVs")
    parser.add_argument("--output_csv", required=True, help="Path to save bankroll simulation log")
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--odds_cap", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default=DEFAULT_STRATEGY)
    parser.add_argument("--plot", action="store_true", help="Show bankroll plot")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    files = [Path(f.strip()) for f in args.input_csvs.split(",") if f.strip()]
    dfs = []

    for f in files:
        try:
            assert_file_exists(f, "value_bets_csv")
            df = pd.read_csv(f)
            df = normalize_columns(df)
            df = patch_winner_column(df)
            df = add_ev_and_kelly(df)
            df = filter_value_bets(df, args.ev_threshold, args.odds_cap, max_margin=1.0)
            dfs.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {f}: {e}")

    if not dfs:
        raise ValueError("❌ No valid input files after normalization and filtering.")

    df = pd.concat(dfs, ignore_index=True)

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        ev_threshold=0.0,
        odds_cap=100.0,
        initial_bankroll=1000.0,
        cap_fraction=0.05
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sim_df.to_csv(output_path, index=False)
    log_success(f"✅ Simulated {len(sim_df)} bets")
    log_success(f"💰 Final bankroll: {final_bankroll:.2f}")
    log_success(f"📉 Max drawdown: {max_drawdown:.2f}")

    png_path = output_path.with_suffix(".png")
    generate_bankroll_plot(sim_df["bankroll"], output_path=png_path)

    if args.plot:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
