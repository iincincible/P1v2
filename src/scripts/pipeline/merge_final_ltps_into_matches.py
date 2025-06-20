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

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would merge final LTPs from {_args.snapshots_csv} into {_args.matches_csv} → {_args.output_csv}"
        )
        return

    matches_path = Path(_args.matches_csv)
    snaps_path = Path(_args.snapshots_csv)
    output_path = Path(_args.output_csv)

    assert_file_exists(matches_path, "matches_csv")
    assert_file_exists(snaps_path, "snapshots_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        matches = pd.read_csv(matches_path)
        log_info(f"📥 Loaded {len(matches)} matches from {matches_path}")
        snapshots = pd.read_csv(snaps_path)
        log_info(f"📥 Loaded {len(snapshots)} snapshots from {snaps_path}")
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
            .rename(columns={"ltp": "ltp_player_1"})
            .drop(columns=["selection_id"])
        )
        merged = (
            merged.merge(
                final_ltp,
                left_on=["market_id", "selection_id_2"],
                right_on=["market_id", "selection_id"],
                how="left",
            )
            .rename(columns={"ltp": "ltp_player_2"})
            .drop(columns=["selection_id"])
        )
    except Exception as e:
        log_error(f"❌ Error merging LTPs: {e}")
        return

    if merged["ltp_player_1"].isna().any() or merged["ltp_player_2"].isna().any():
        log_warning("⚠️ Some LTP values are missing after merge")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)
        log_success(f"✅ Saved matches with LTPs to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save merged CSV: {e}")


if __name__ == "__main__":
    main()
