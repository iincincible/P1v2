# src/scripts/pipeline/merge_final_ltps_into_matches.py

import pandas as pd
from scripts.utils.logger import log_info
from scripts.utils.schema import normalize_columns, enforce_schema


def merge_final_ltps(df_matches: pd.DataFrame, df_snaps: pd.DataFrame) -> pd.DataFrame:
    """
    Merge final LTPs into matches.
    """
    df_matches = normalize_columns(df_matches)
    df_snaps = normalize_columns(df_snaps)
    final_snaps = (
        df_snaps.sort_values(["match_id", "selection_id", "timestamp"])
        .groupby(["match_id", "selection_id"], as_index=False)
        .last()[["match_id", "selection_id", "ltp"]]
    )
    df_merged = df_matches.merge(
        final_snaps,
        on=["match_id", "selection_id"],
        how="left",
        suffixes=("", "_final"),
    )
    df_merged.rename(columns={"ltp_final": "final_ltp"}, inplace=True)
    return enforce_schema(df_merged, "merged_matches")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Merge final LTPs into matches")
    parser.add_argument("--matches_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    df_matches = pd.read_csv(args.matches_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)
    result = merge_final_ltps(df_matches, df_snaps)
    if not args.dry_run:
        result.to_csv(args.output_csv, index=False)
        log_info(f"Merged matches written to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
