# src/scripts/pipeline/match_selection_ids.py

import pandas as pd
from scripts.utils.logger import log_info
from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)


def assign_selection_ids(
    df_matches: pd.DataFrame, df_snaps: pd.DataFrame
) -> pd.DataFrame:
    """
    Assign Betfair selection IDs to matches based on snapshot data.
    """
    df_matches = normalize_columns(df_matches)
    df_snaps = normalize_columns(df_snaps)
    market_map = build_market_runner_map(df_snaps)
    df_matches = df_matches.copy()
    df_matches["selection_id_1"] = df_matches.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_1"]
        ),
        axis=1,
    )
    df_matches["selection_id_2"] = df_matches.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_2"]
        ),
        axis=1,
    )
    return enforce_schema(df_matches, "matches_with_ids")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Assign selection IDs.")
    parser.add_argument("--matches_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    df_matches = pd.read_csv(args.matches_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)
    result = assign_selection_ids(df_matches, df_snaps)
    if not args.dry_run:
        result.to_csv(args.output_csv, index=False)
        log_info(f"Wrote matches with IDs to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
