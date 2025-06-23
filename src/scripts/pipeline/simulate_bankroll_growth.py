import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists, output_file_guard
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot

@output_file_guard(output_arg="output_csv")
def simulate_bankroll_growth(
    value_bets_csv,
    output_csv,
    overwrite=False,
    dry_run=False,
):
    assert_file_exists(value_bets_csv, "value_bets_csv")
    df = pd.read_csv(value_bets_csv)
    log_info(f"📥 Loaded {len(df)} value bets from {value_bets_csv}")

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(df)
    log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
    log_info(f"📉 Max drawdown: {max_drawdown:.2f}")

    sim_df.to_csv(output_csv, index=False)
    log_success(f"✅ Saved bankroll simulation to {output_csv}")

    # Plot
    try:
        plot_path = Path(output_csv).with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=plot_path)
        log_success(f"🖼️ Saved bankroll plot to {plot_path}")
    except Exception as e:
        log_warning(f"⚠️ Could not generate bankroll plot: {e}")

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Simulate bankroll growth from value bets."
    )
    parser.add_argument(
        "--value_bets_csv", required=True, help="Path to value bets CSV"
    )
    parser.add_argument(
        "--output_csv", required=True, help="Path to save bankroll simulation CSV"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    simulate_bankroll_growth(
        value_bets_csv=_args.value_bets_csv,
        output_csv=_args.output_csv,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
