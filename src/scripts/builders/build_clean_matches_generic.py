"""
CLI entrypoint for cleaning match snapshot CSVs.
"""

import argparse
import sys
import pandas as pd
from scripts.utils.logger import log_dryrun
from scripts.utils.normalize_columns import (
    normalize_columns,
    patch_winner_column,
    assert_required_columns,
)


def process_snapshots(
    snapshots_csv: str,
    tour: str,
    tournament: str,
    year: int,
    output_csv: str,
    verbose: bool = False,
) -> None:
    """
    Load, normalize, and write cleaned snapshots.
    """
    df = pd.read_csv(snapshots_csv)
    if verbose:
        print(f"Loaded {len(df)} rows from {snapshots_csv}")

    df = normalize_columns(df)
    df = patch_winner_column(df)
    assert_required_columns(df, context=f"Cleaning {tour} {tournament} {year}")

    df.to_csv(output_csv, index=False)
    if verbose:
        print(f"Wrote cleaned data ({len(df)} rows) to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Clean match snapshots CSV.")
    parser.add_argument("--tour", required=True, help="Tour name, e.g., atp, wta")
    parser.add_argument(
        "--tournament", required=True, help="Tournament identifier, e.g., ausopen"
    )
    parser.add_argument(
        "--year", type=int, required=True, help="Year of the tournament"
    )
    parser.add_argument(
        "--snapshots",
        dest="snapshots_csv",
        required=True,
        help="Path to raw snapshots CSV",
    )
    parser.add_argument("--output_csv", required=True, help="Path to write cleaned CSV")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing output",
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose logs")
    args = parser.parse_args()

    if args.dry_run:
        log_dryrun(
            f"Would process {args.snapshots_csv} for {args.tour} {args.tournament} {args.year} "
            f"and write to {args.output_csv}"
        )
        sys.exit(0)

    process_snapshots(
        args.snapshots_csv,
        args.tour,
        args.tournament,
        args.year,
        args.output_csv,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
