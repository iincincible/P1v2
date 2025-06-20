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
    should_run,
    assert_file_exists,
    assert_columns_exist,
)
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly


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

    files = glob.glob(_args.value_bets_glob)
    if not files:
        raise ValueError(
            f"❌ No value bet files found matching: {_args.value_bets_glob}"
        )

    # Dry-run: just log and exit
    if _args.dry_run:
        log_dryrun(
            f"Would summarize {len(files)} files matching "
            f"'{_args.value_bets_glob}' into {_args.output_csv}"
        )
        return

    output_path = Path(_args.output_csv)
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

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

            # Ensure consistent scoring columns
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

    # Aggregate by match
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

    # Reattach player names
    firsts = combined.drop_duplicates("match_id")[
        ["match_id", "player_1", "player_2"]
    ].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()

    # Print preview
    if _args.top_n > 0:
        preview = summary.sort_values(by="total_profit", ascending=False).head(
            _args.top_n
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

    # Write output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(output_path, index=False)
        log_success(f"✅ Saved match-level summary to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save summary to {output_path}: {e}")


if __name__ == "__main__":
    main()
