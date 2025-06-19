import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.constants import DEFAULT_FIXED_STAKE, DEFAULT_STRATEGY
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly

def main():
    """Simulate bankroll using all value bets, ensuring consistent winner/EV columns."""
    parser = argparse.ArgumentParser(description="Simulate bankroll using all value bets from glob.")
    parser.add_argument("--value_bets_csv", required=True, help="Path to full value bets CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save simulation result")
    parser.add_argument("--strategy", choices=["flat", "kelly"], default=DEFAULT_STRATEGY)
    parser.add_argument("--fixed_stake", type=float, default=DEFAULT_FIXED_STAKE)
    add_common_flags(parser)
    args = parser.parse_args()

    value_bets_path = Path(args.value_bets_csv)
    output_path = Path(args.output_csv)

    assert_file_exists(value_bets_path, "value_bets_csv")
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    df = pd.read_csv(value_bets_path)
    df = normalize_columns(df)
    df = add_ev_and_kelly(df)
    df = patch_winner_column(df)

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        initial_bankroll=1000.0,
        ev_threshold=0.0,
        odds_cap=100.0,
        cap_fraction=0.05
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sim_df.to_csv(output_path, index=False)
    png_path = output_path.with_suffix(".png")
    generate_bankroll_plot(sim_df["bankroll"], output_path=png_path)

    print(f"💰 Final bankroll: {final_bankroll:.2f}")
    print(f"📉 Max drawdown: {max_drawdown:.2f}")

if __name__ == "__main__":
    main()
