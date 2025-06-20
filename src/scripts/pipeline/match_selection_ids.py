import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_warning,
    log_error,
    log_success,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Match player names to Betfair selection IDs."
    )
    parser.add_argument(
        "--merged_csv",
        required=True,
        help="Input match CSV with player names",
    )
    parser.add_argument(
        "--snapshots_csv",
        required=True,
        help="Parsed Betfair snapshots CSV",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        help="Path to save selection ID mapping",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run: just log intent
    if _args.dry_run:
        log_dryrun(
            f"Would load matches from {_args.merged_csv}, snapshots from {_args.snapshots_csv}, "
            f"and write selection IDs to {_args.output_csv}"
        )
        return

    merged_path = Path(_args.merged_csv)
    snaps_path = Path(_args.snapshots_csv)
    output_path = Path(_args.output_csv)

    # Existence checks
    assert_file_exists(merged_path, "merged_csv")
    assert_file_exists(snaps_path, "snapshots_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        df_matches = pd.read_csv(merged_path)
        log_info(f"📥 Loaded {len(df_matches)} matches from {merged_path}")
    except Exception as e:
        log_error(f"❌ Failed to read {merged_path}: {e}")
        return

    try:
        df_snaps = pd.read_csv(snaps_path)
        log_info(f"📥 Loaded {len(df_snaps)} snapshots from {snaps_path}")
    except Exception as e:
        log_error(f"❌ Failed to read {snaps_path}: {e}")
        return

    if "match_id" not in df_matches.columns:
        log_error("❌ 'match_id' column is required in merged_csv")
        return

    # Build mapping from snapshots
    log_info("🔍 Building market→runner map")
    market_runner_map = build_market_runner_map(df_snaps)

    # Apply matching
    log_info("🔍 Matching selection IDs for each player")
    tqdm.pandas(desc="Matching IDs")
    df_matches["selection_id_1"] = df_matches.progress_apply(
        lambda row: match_player_to_selection_id(
            market_runner_map, row["market_id"], row["player_1"]
        ),
        axis=1,
    )
    df_matches["selection_id_2"] = df_matches.progress_apply(
        lambda row: match_player_to_selection_id(
            market_runner_map, row["market_id"], row["player_2"]
        ),
        axis=1,
    )

    unmatched_1 = df_matches["selection_id_1"].isna().sum()
    unmatched_2 = df_matches["selection_id_2"].isna().sum()
    if unmatched_1 or unmatched_2:
        log_warning(f"⚠️ Unmatched selection_id_1: {unmatched_1}")
        log_warning(f"⚠️ Unmatched selection_id_2: {unmatched_2}")

    # Save results
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_matches.to_csv(output_path, index=False)
        log_success(f"✅ Saved selection ID mappings to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save selection ID mappings: {e}")


if __name__ == "__main__":
    main()
