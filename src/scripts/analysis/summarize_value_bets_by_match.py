import pandas as pd
import glob
from pathlib import Path

from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning, setup_logging


def run_summarize_value_bets_by_match(files, top_n: int = 10) -> pd.DataFrame:
    """
    Summarize value bets by match across multiple files (pure function).
    """
    all_bets = []
    for filepath in files:
        try:
            df = pd.read_csv(filepath)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            all_bets.append(df)
        except Exception as e:
            log_warning(f"Skipping {filepath}: {e}")
    if not all_bets:
        raise ValueError(
            "No valid value bet files found after normalization and validation."
        )

    combined = pd.concat(all_bets, ignore_index=True)
    enforce_schema(combined, "value_bets")
    log_info(f"Loaded {len(combined)} total bets across all files.")

    grouped = combined.groupby("match_id").agg(
        num_bets=("expected_value", "count"),
        avg_ev=("expected_value", "mean"),
        max_confidence=("predicted_prob", "max"),
        any_win=("winner", "max"),
        total_staked=(
            ("kelly_stake", "sum")
            if "kelly_stake" in combined.columns
            else ("expected_value", "sum")
        ),
        total_profit=lambda g: (
            ((g["winner"] * (g["odds"] - 1)) - (~g["winner"].astype(bool)) * 1.0).sum()
            if "winner" in combined.columns and "odds" in combined.columns
            else 0
        ),
    )
    firsts = combined.drop_duplicates("match_id")[
        ["match_id", "player_1", "player_2"]
    ].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()
    if top_n > 0:
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


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Summarize value bets by match across multiple files."
    )
    parser.add_argument("--value_bets_glob", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--top_n", type=int, default=10)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    setup_logging(level="DEBUG" if args.verbose else "INFO", json_logs=args.json_logs)
    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError(f"No value bet files found matching: {args.value_bets_glob}")
    summary = run_summarize_value_bets_by_match(files, top_n=args.top_n)
    if not args.dry_run:
        Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.output_csv, index=False)
        log_success(f"Saved match-level summary to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
