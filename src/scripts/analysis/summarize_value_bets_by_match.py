import argparse
import pandas as pd
import glob
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import (
    add_common_flags,
    output_file_guard,
    assert_file_exists,
    assert_columns_exist,
)
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly

@output_file_guard(output_arg="output_csv")
def summarize_value_bets_by_match(
    value_bets_glob,
    output_csv,
    top_n=10,
    overwrite=False,
    dry_run=False,
):
    files = glob.glob(value_bets_glob)
    if not files:
        raise ValueError(
            f"❌ No value bet files found matching: {value_bets_glob}"
        )

    all_bets = []
    for filepath in files:
        try:
            assert_file_exists(filepath, "value_bets_csv")
            df = pd.read_csv(filepath)
        except Exception as e:
            log_warning(f"⚠️ Skipping {filepath}: {e}")
            continue

        try:
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = patch_winner_column(df)

            required_cols = [
                "match_id",
                "player_1",
                "player_2",
                "odds",
                "expected_value",
            ]
            assert_columns_exist(df, required_cols, context=filepath)

            if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
                df["confidence_score"] = df["predicted_prob"]
            if "kelly_stake" not in df.columns:
                df["kelly_stake"] = 1.0

            all_bets.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {filepath}: {e}")

    if not all_bets:
        raise ValueError(
            "❌ No valid value bet files found after normalization and validation."
        )

    combined = pd.concat(all_bets, ignore_index=True)
    log_info(f"📊 Loaded {len(combined)} total bets across all files")

    grouped = combined.groupby("match_id").agg(
        num_bets=("expected_value", "count"),
        avg_ev=("expected_value", "mean"),
        max_confidence=("confidence_score", "max"),
        any_win=("winner", "max"),
        total_staked=("kelly_stake", "sum"),
        total_profit=(
            lambda g: (
                (g["winner"] * (g["odds"] - 1)) - (~g["winner"].astype(bool)) * 1.0
            ).sum()
        ),
    )

    firsts = combined.drop_duplicates("match_id")[
        ["match_id", "player_1", "player_2"]
    ].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()

    if top_n > 0:
        preview = summary.sort_values(by="total_profit", ascending=False).head(
            top_n
        )
        log_info("\n📊 Top Matches by Profit:")
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

    summary.to_csv(output_csv, index=False)
    log_success(f"✅ Saved match-level summary to {output_csv}")

def main(args=None):
    parser = argparse.ArgumentParser(description="Summarize value bets by match.")
    parser.add_argument(
        "--value_bets_glob",
        required=True,
        help="Glob pattern for *_value_bets.csv files",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        help="Path to save grouped match summary",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Print top-N matches by profit (0 to disable)",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    summarize_value_bets_by_match(
        value_bets_glob=_args.value_bets_glob,
        output_csv=_args.output_csv,
        top_n=_args.top_n,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
