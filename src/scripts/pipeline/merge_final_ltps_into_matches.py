import argparse
import pandas as pd
import logging
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists, output_file_guard
from scripts.utils.normalize_columns import enforce_canonical_columns

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)

@output_file_guard(output_arg="output_csv")
def merge_final_ltps_into_matches(
    matches_csv,
    snapshots_csv,
    output_csv,
    overwrite=False,
    dry_run=False,
):
    assert_file_exists(matches_csv, "matches_csv")
    assert_file_exists(snapshots_csv, "snapshots_csv")

    try:
        matches = pd.read_csv(matches_csv)
        log_info(f"📥 Loaded {len(matches)} matches from {matches_csv}")
        snapshots = pd.read_csv(snapshots_csv)
        log_info(f"📥 Loaded {len(snapshots)} snapshots from {snapshots_csv}")
    except Exception as e:
        log_error(f"❌ Failed to read inputs: {e}")
        return

    if "market_id" not in matches.columns or "market_id" not in snapshots.columns:
        log_error("❌ Both files must contain 'market_id'")
        return

    try:
        final_ltp = (
            snapshots.sort_values("timestamp")
            .groupby(["market_id", "selection_id"])
            .last()
            .reset_index()[["market_id", "selection_id", "ltp"]]
        )
    except Exception as e:
        log_error(f"❌ Error computing final LTPs: {e}")
        return

    try:
        merged = (
            matches.merge(
                final_ltp,
                left_on=["market_id", "selection_id_1"],
                right_on=["market_id", "selection_id"],
                how="left",
            )
        )
        merged = merged.drop(columns=[c for c in ["selection_id"] if c in merged.columns])

        merged = (
            merged.merge(
                final_ltp,
                left_on=["market_id", "selection_id_2"],
                right_on=["market_id", "selection_id"],
                how="left",
            )
        )
        merged = merged.drop(columns=[c for c in ["selection_id"] if c in merged.columns])

        # Fix column names for output contract
        if "ltp_x" in merged.columns and "ltp_y" in merged.columns:
            merged = merged.rename(columns={"ltp_x": "ltp_player_1", "ltp_y": "ltp_player_2"})
    except Exception as e:
        log_error(f"❌ Error merging LTPs: {e}")
        return

    # Optional: warn if missing values after merge
    if "ltp_player_1" in merged.columns and merged["ltp_player_1"].isna().any():
        log_warning("⚠️ Some ltp_player_1 values are missing after merge")
    if "ltp_player_2" in merged.columns and merged["ltp_player_2"].isna().any():
        log_warning("⚠️ Some ltp_player_2 values are missing after merge")

    # No canonical column enforcement here as this is intermediate, but add if needed.
    merged.to_csv(output_csv, index=False)
    log_success(f"✅ Saved matches with LTPs to {output_csv}")

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Merge final LTPs from snapshots into matches CSV."
    )
    parser.add_argument(
        "--matches_csv", required=True, help="Path to clean matches CSV"
    )
    parser.add_argument(
        "--snapshots_csv", required=True, help="Path to parsed Betfair snapshots"
    )
    parser.add_argument(
        "--output_csv", required=True, help="Path to save enriched matches CSV"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    merge_final_ltps_into_matches(
        matches_csv=_args.matches_csv,
        snapshots_csv=_args.snapshots_csv,
        output_csv=_args.output_csv,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
