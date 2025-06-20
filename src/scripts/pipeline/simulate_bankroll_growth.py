import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,  # ← Added this
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot


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

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would simulate bankroll from {_args.value_bets_csv} → {_args.output_csv}"
        )
        return

    bets_path = Path(_args.value_bets_csv)
    output_path = Path(_args.output_csv)

    assert_file_exists(bets_path, "value_bets_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        df = pd.read_csv(bets_path)
        log_info(f"📥 Loaded {len(df)} value bets from {bets_path}")
    except Exception as e:
        log_error(f"❌ Failed to read value bets: {e}")
        return

    try:
        sim_df, final_bankroll, max_drawdown = simulate_bankroll(df)
        log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
        log_info(f"📉 Max drawdown: {max_drawdown:.2f}")
    except Exception as e:
        log_error(f"❌ Simulation failed: {e}")
        return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sim_df.to_csv(output_path, index=False)
        log_success(f"✅ Saved bankroll simulation to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save simulation CSV: {e}")
        return

    # Plot
    try:
        plot_path = output_path.with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=plot_path)
        log_success(f"🖼️ Saved bankroll plot to {plot_path}")
    except Exception as e:
        log_warning(f"⚠️ Could not generate bankroll plot: {e}")


if __name__ == "__main__":
    main()
