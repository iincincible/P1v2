# File: src/scripts/builders/build_clean_matches_generic.py

import argparse
import hashlib
import logging
from pathlib import Path

from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.cli_utils import (
    add_common_flags,
    assert_file_exists,
    output_file_guard,
    should_run,
)
from scripts.utils.logger import (
    log_dryrun,
    log_error,
    log_info,
    log_success,
    log_warning,
)
from scripts.utils.normalize_columns import (
    CANONICAL_REQUIRED_COLUMNS,
)

logging.basicConfig(level=logging.INFO)


def generate_match_id(row) -> str:
    key = f"{row['tournament']}_{row['year']}_{row['player_1']}_{row['player_2']}_{row['market_id']}"
    return hashlib.md5(key.encode()).hexdigest()


def patch_missing_canonical_columns(df):
    """Ensure all required canonical columns are present (as NaN if not computable)."""
    for col in CANONICAL_REQUIRED_COLUMNS:
        if col not in df.columns:
            log_warning(
                f"[PATCH] Adding missing canonical column: {col} (filled with NaN)"
            )
            df[col] = float("nan")
    return df


@output_file_guard(output_arg="output_csv")
def build_matches(
    tour,
    tournament,
    year,
    snapshots_csv,
    output_csv,
    sackmann_csv=None,
    alias_csv=None,
    player_stats_csv=None,
    snapshot_only=False,
    fuzzy_match=False,
    overwrite=False,
    dry_run=False,
):
    output_path = Path(output_csv)
    if dry_run:
        log_dryrun(f"Would build clean matches for {tournament} {year} → {output_path}")
        return
    if not should_run(output_path, overwrite, dry_run):
        return

    assert_file_exists(snapshots_csv, "snapshots_csv")
    if sackmann_csv and not snapshot_only:
        assert_file_exists(sackmann_csv, "sackmann_csv")
    if alias_csv:
        assert_file_exists(alias_csv, "alias_csv")
    if player_stats_csv:
        assert_file_exists(player_stats_csv, "player_stats_csv")

    try:
        df_matches = build_matches_from_snapshots(
            snapshot_csv=snapshots_csv,
            sackmann_csv=sackmann_csv,
            alias_csv=alias_csv,
            snapshot_only=snapshot_only,
            fuzzy_match=fuzzy_match,
        )

        # --- DEBUG: print columns and head ---
        print(
            "\n[DEBUG] Columns from build_matches_from_snapshots:",
            df_matches.columns.tolist(),
        )
        print("[DEBUG] Number of rows:", len(df_matches))
        print(df_matches.head(3))
        # --- END DEBUG ---

        # Add tournament/year for match_id generation
        df_matches["tournament"] = tournament
        df_matches["year"] = year

        # Map runner_1/runner_2 to player_1/player_2 before deduplication
        df_matches["player_1"] = df_matches["runner_1"]
        df_matches["player_2"] = df_matches["runner_2"]

        # Deduplicate by all key columns
        dedup_cols = ["tournament", "year", "player_1", "player_2", "market_id"]
        df_matches = df_matches.drop_duplicates(subset=dedup_cols)

        # Validate required columns for match_id
        for col in ["market_id", "player_1", "player_2"]:
            if col not in df_matches.columns:
                raise ValueError(f"Missing column in match build: {col}")

        # Generate unique match IDs
        df_matches["match_id"] = df_matches.apply(generate_match_id, axis=1)
        if df_matches["match_id"].duplicated().any():
            dupes = df_matches[df_matches["match_id"].duplicated(keep=False)]
            raise ValueError(f"Duplicate match_ids found:\n{dupes.head()}")

        log_info(f"📏 Built {len(df_matches)} matches")

        # Patch canonical columns (always present, even if not computable yet)
        df_matches = patch_missing_canonical_columns(df_matches)

        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_matches.to_csv(output_path, index=False)
        log_success(f"✅ Saved {len(df_matches)} matches to {output_path}")

    except Exception as e:
        import traceback

        print("[EXCEPTION CAUGHT IN build_matches]")
        traceback.print_exc()
        log_error(f"❌ Failed to build matches: {e}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Build matches from Betfair snapshots and optional results."
    )
    parser.add_argument("--tour", required=True)
    parser.add_argument("--tournament", required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--sackmann_csv", help="Optional match results file")
    parser.add_argument("--alias_csv", help="Optional alias map file")
    parser.add_argument("--player_stats_csv", help="Optional stats feature CSV")
    parser.add_argument("--snapshot_only", action="store_true")
    parser.add_argument("--fuzzy_match", action="store_true")
    parser.add_argument("--output_csv", required=True)
    add_common_flags(parser)
    _args = parser.parse_args(args)
    build_matches(
        tour=_args.tour,
        tournament=_args.tournament,
        year=_args.year,
        snapshots_csv=_args.snapshots_csv,
        output_csv=_args.output_csv,
        sackmann_csv=_args.sackmann_csv,
        alias_csv=_args.alias_csv,
        player_stats_csv=_args.player_stats_csv,
        snapshot_only=_args.snapshot_only,
        fuzzy_match=_args.fuzzy_match,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )


if __name__ == "__main__":
    main()
