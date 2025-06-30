# src/scripts/pipeline/match_selection_ids.py

import pandas as pd

from scripts.utils.logger import log_info
from scripts.utils.schema import enforce_schema, normalize_columns
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)


def assign_selection_ids(
    matches_df: pd.DataFrame, snapshots_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Assigns Betfair selection IDs to players in a matches DataFrame.

    It uses a snapshots DataFrame to create a mapping between player names and
    their selection IDs for each market.

    :param matches_df: DataFrame of matches, containing player names and market_id.
    :param snapshots_df: DataFrame of raw snapshot data, used to build the mapping.
    :return: The matches_df with 'selection_id_1' and 'selection_id_2' columns added.
    """
    matches_df = normalize_columns(matches_df)
    snapshots_df = normalize_columns(snapshots_df)
    market_map = build_market_runner_map(snapshots_df)

    matches_df = matches_df.copy()
    matches_df["selection_id_1"] = matches_df.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_1"]
        ),
        axis=1,
    )
    matches_df["selection_id_2"] = matches_df.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_2"]
        ),
        axis=1,
    )
    return enforce_schema(matches_df, "matches_with_ids")


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
