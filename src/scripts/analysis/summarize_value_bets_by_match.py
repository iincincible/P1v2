import argparse
from pathlib import Path

import pandas as pd

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.decorators import with_logging
from scripts.utils.file_utils import load_dataframes
from scripts.utils.logger import log_info, log_success
from scripts.utils.schema import enforce_schema, normalize_columns


def run_summarize_value_bets_by_match(
    df: pd.DataFrame, top_n: int = 10
) -> pd.DataFrame:
    """
    Summarize value bets by match from a combined DataFrame (pure function).
    """
    df = normalize_columns(df)
    df = add_ev_and_kelly(df)
    enforce_schema(df, "value_bets")

    log_info(f"Processing {len(df)} total bets.")

    grouped = df.groupby("match_id").agg(
        num_bets=("expected_value", "count"),
        avg_ev=("expected_value", "mean"),
        max_confidence=("predicted_prob", "max"),
        any_win=("winner", "max"),
        total_staked=(
            ("kelly_stake", "sum")
            if "kelly_stake" in df.columns
            else ("expected_value", "sum")
        ),
        total_profit=lambda g: (
            ((g["winner"] * (g["odds"] - 1)) - (~g["winner"].astype(bool)) * 1.0).sum()
            if "winner" in df.columns and "odds" in df.columns
            else 0
        ),
    )
    firsts = df.drop_duplicates("match_id")[
        ["match_id", "player_1", "player_2"]
    ].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()
    if top_n > 0 and not summary.empty:
        preview = summary.sort_values(by="total_profit", ascending=False).head(top_n)
        log_info("\nTop Matches by Profit:")
        log_info(
            preview[
                [
                    "match_id",
                    "player_1",
                    "player_2",
                    "num_bets",
                    "avg_ev",
                    "total_profit",
                ]
            ].to_string(index=False)
        )
    return summary


@with_logging
def main_cli():
    parser = argparse.ArgumentParser(
        description="Summarize value bets by match across multiple files."
    )
    parser.add_argument(
        "--value_bets_glob",
        required=True,
        help="Glob pattern for input value bet CSV files (e.g., 'data/*_value_bets.csv').",
    )
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--top_n", type=int, default=10)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()

    combined_bets = load_dataframes(args.value_bets_glob)
    summary = run_summarize_value_bets_by_match(combined_bets, top_n=args.top_n)

    if not args.dry_run:
        Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.output_csv, index=False)
        log_success(f"Saved match-level summary to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
