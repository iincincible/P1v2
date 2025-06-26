import pandas as pd

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)


def build_matches_from_snapshots(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a matches DataFrame from raw snapshot data.

    Args:
        snapshot_df: DataFrame containing raw snapshots with columns ['match_id', 'market', 'selection', ...].

    Returns:
        A DataFrame of matches with enforced schema.
    """
    # Group raw snapshots into matches
    grouped = snapshot_df.groupby(
        ["match_id", "market", "selection"], as_index=False
    ).agg(
        ltp=("price", "last"), volume=("volume", "sum"), timestamp=("timestamp", "max")
    )

    # Debug information
    logger.debug("Columns returned: %s", grouped.columns.tolist())
    logger.debug("Number of rows: %d", len(grouped))
    logger.debug("First few rows:\n%s", grouped.head(3))

    # Enforce canonical schema for matches
    matches_df = SchemaManager.patch_schema(grouped, schema_name="matches")
    return matches_df


@guarded_run
def main(input_path: str, output_path: str, dry_run: bool = False):
    """
    Entry point to build matches from snapshot CSV.

    Args:
        input_path: Path to the input snapshot CSV file.
        output_path: Path to write the output matches CSV.
        dry_run: If True, process without writing the file.
    """
    # Load raw snapshots
    df = pd.read_csv(input_path)
    logger.info("Loaded %d snapshots from %s", len(df), input_path)

    # Build matches
    matches_df = build_matches_from_snapshots(df)

    # Write or skip output
    if dry_run:
        logger.info("Dry-run mode active; no file written.")
    else:
        matches_df.to_csv(output_path, index=False)
        logger.info("Matches written to %s", output_path)


if __name__ == "__main__":
    main()
