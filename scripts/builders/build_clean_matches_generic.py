import argparse
import pandas as pd
from pathlib import Path
import sys
import hashlib

# Add root to import path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.logger import log_info, log_success, log_error
from scripts.utils.paths import get_snapshot_csv_path
from scripts.utils.cli_utils import assert_file_exists, should_run, add_common_flags, assert_columns_exist


def generate_match_id(row):
    """
    Deterministically hashes match row fields into a match_id.
    """
    key = f"{row['tournament']}_{row['year']}_{row['player_1']}_{row['player_2']}_{row['market_id']}"
    return hashlib.md5(key.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Build matches from Betfair snapshots and optional results.")
    parser.add_argument("--tour", required=True)
    parser.add_argument("--tournament", required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--snapshots_csv", required=False, help="Path to parsed Betfair snapshots")
    parser.add_argument("--sackmann_csv", required=False, help="Optional match results file for outcome labels")
    parser.add_argument("--alias_csv", required=False, help="Optional alias map file")
    parser.add_argument("--player_stats_csv", required=False, help="Optional stats feature CSV")
    parser.add_argument("--snapshot_only", action="store_true")
    parser.add_argument("--fuzzy_match", action="store_true")
    parser.add_argument("--output_csv", required=True)
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    label = f"{args.tournament}_{args.year}_{args.tour}"
    snapshots_csv = args.snapshots_csv or get_snapshot_csv_path(label)
    assert_file_exists(snapshots_csv, "snapshots_csv")

    if args.sackmann_csv and not args.snapshot_only:
        assert_file_exists(args.sackmann_csv, "sackmann_csv")
    if args.alias_csv:
        assert_file_exists(args.alias_csv, "alias_csv")
    if args.player_stats_csv:
        assert_file_exists(args.player_stats_csv, "player_stats_csv")

    try:
        df_matches = build_matches_from_snapshots(
            tour=args.tour,
            tournament=args.tournament,
            year=int(args.year),
            snapshots_csv=snapshots_csv,
            sackmann_csv=args.sackmann_csv,
            alias_csv=args.alias_csv,
            player_stats_csv=args.player_stats_csv,
            snapshot_only=args.snapshot_only,
            fuzzy_match=args.fuzzy_match,
        )

        # === Integrity checks ===
        required = ["market_id", "player_1", "player_2"]
        assert_columns_exist(df_matches, required, context="match build")

        df_matches["match_id"] = df_matches.apply(generate_match_id, axis=1)
        if df_matches["match_id"].duplicated().any():
            dupes = df_matches[df_matches["match_id"].duplicated(keep=False)]
            raise ValueError(f"❌ Duplicate match_ids found:\n{dupes[['match_id', 'player_1', 'player_2']].head()}")

        log_info(f"📏 Built {len(df_matches)} matches")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_matches.to_csv(output_path, index=False)
        log_success(f"✅ Saved {len(df_matches)} matches to {output_path}")

    except Exception as e:
        log_error(f"❌ Failed to build matches for {label}")
        log_error(str(e))


if __name__ == "__main__":
    main()
