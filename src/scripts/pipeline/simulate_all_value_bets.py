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
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.constants import DEFAULT_STRATEGY
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Simulate bankroll using all value bets from CSV."
    )
    parser.add_argument(
        "--value_bets_csv",
        required=True,
        help="Path to full value bets CSV",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        help="Path to save simulation result CSV",
    )
    parser.add_argument(
        "--strategy",
        choices=["flat", "kelly"],
        default=DEFAULT_STRATEGY,
        help="Staking strategy",
    )
    parser.add_argument(
        "--initial_bankroll",
        type=float,
        default=1000.0,
        help="Starting bankroll for simulation",
    )
    parser.add_argument(
        "--ev_threshold",
        type=float,
        default=0.0,
        help="Minimum EV threshold for bets",
    )
    parser.add_argument(
        "--odds_cap",
        type=float,
        default=100.0,
        help="Maximum odds allowed",
    )
    parser.add_argument(
        "--cap_fraction",
        type=float,
        default=0.05,
        help="Max fraction of bankroll per Kelly bet",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run: log intent and exit
    if _args.dry_run:
        log_dryrun(
            f"Would simulate bankroll from {_args.value_bets_csv} "
            f"→ {_args.output_csv} using strategy {_args.strategy}"
        )
        return

    input_path = Path(_args.value_bets_csv)
    output_path = Path(_args.output_csv)

    assert_file_exists(input_path, "value_bets_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    # Load & normalize
    try:
        df = pd.read_csv(input_path)
        log_info(f"📥 Loaded {len(df)} value bets from {input_path}")
        df = normalize_columns(df)
        df = add_ev_and_kelly(df)
        df = patch_winner_column(df)
    except Exception as e:
        log_error(f"❌ Failed to prepare value bets: {e}")
        return

    # Run simulation
    try:
        sim_df, final_bankroll, max_drawdown = simulate_bankroll(
            sim_df=df,
            strategy=_args.strategy,
            initial_bankroll=_args.initial_bankroll,
            ev_threshold=_args.ev_threshold,
            odds_cap=_args.odds_cap,
            cap_fraction=_args.cap_fraction,
        )
        log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
        log_info(f"📉 Max drawdown: {max_drawdown:.2f}")
    except Exception as e:
        log_error(f"❌ Simulation failed: {e}")
        return

    # Save CSV
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sim_df.to_csv(output_path, index=False)
        log_success(f"✅ Saved simulation to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save simulation CSV: {e}")
        return

    # Save plot
    try:
        plot_path = output_path.with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=plot_path)
        log_success(f"🖼️ Saved bankroll plot to {plot_path}")
    except Exception as e:
        log_warning(f"⚠️ Could not generate bankroll plot: {e}")


if __name__ == "__main__":
    main()
