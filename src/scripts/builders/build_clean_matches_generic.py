# src/scripts/builders/build_clean_matches_generic.py

import pandas as pd
from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.logger import log_info
from scripts.utils.schema import normalize_columns, enforce_schema


def build_clean_matches(df_snapshots: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw snapshots DataFrame into canonical matches DataFrame.
    """
    df_snapshots = normalize_columns(df_snapshots)
    matches_df = build_matches_from_snapshots(df_snapshots)
    return enforce_schema(matches_df, "matches")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build clean matches from snapshot CSV."
    )
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    df_snapshots = pd.read_csv(args.snapshots_csv)
    matches_df = build_clean_matches(df_snapshots)
    if not args.dry_run:
        matches_df.to_csv(args.output_csv, index=False)
        log_info(f"Wrote {len(matches_df)} matches to {args.output_csv}")
    else:
        log_info(
            f"[DRY-RUN] Would write {len(matches_df)} matches to {args.output_csv}"
        )


if __name__ == "__main__":
    main_cli()
