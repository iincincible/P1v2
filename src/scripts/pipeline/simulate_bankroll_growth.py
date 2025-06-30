# src/scripts/pipeline/simulate_bankroll_growth.py

import argparse

import pandas as pd

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.constants import DEFAULT_INITIAL_BANKROLL
from scripts.utils.logger import log_info
from scripts.utils.schema import enforce_schema, normalize_columns


def simulate_bankroll_growth(
    df: pd.DataFrame, initial_bankroll: float = DEFAULT_INITIAL_BANKROLL
) -> pd.DataFrame:
    """
    Simulate bankroll growth from value bet DataFrame.
    """
    df = normalize_columns(df)
    df_metrics = add_ev_and_kelly(df)
    df_metrics = df_metrics.copy()
    df_metrics.insert(0, "bankroll", initial_bankroll)
    for idx in df_metrics.index[1:]:
        prev_bank = df_metrics.at[idx - 1, "bankroll"]
        kelly = df_metrics.at[idx - 1, "kelly_fraction"]
        bet_amount = prev_bank * kelly
        outcome = df_metrics.at[idx - 1, "winner"]
        odds = df_metrics.at[idx - 1, "odds"]
        pnl = bet_amount * (odds - 1) * outcome - bet_amount * (1 - outcome)
        df_metrics.at[idx, "bankroll"] = prev_bank + pnl
    return enforce_schema(df_metrics, schema_name="simulations")


def main_cli():
    parser = argparse.ArgumentParser(description="Simulate bankroll growth")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument(
        "--initial_bankroll",
        type=float,
        default=DEFAULT_INITIAL_BANKROLL,
        help="The starting bankroll for the simulation.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.input_csv)
    result = simulate_bankroll_growth(df, initial_bankroll=args.initial_bankroll)
    if not args.dry_run:
        result.to_csv(args.output_csv, index=False)
        log_info(f"Simulation written to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
