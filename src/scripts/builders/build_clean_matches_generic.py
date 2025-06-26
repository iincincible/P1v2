import pandas as pd
from pathlib import Path

from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)


@guarded_run
def main(
    snapshots_csv: str,
    output_csv: str,
    dry_run: bool = False,
    overwrite: bool = False,
):
    """
    Build matches from Betfair snapshots and optional results.

    Args:
        snapshots_csv: Path to the input snapshot CSV file.
        output_csv: Path to write the output matches CSV file.
        dry_run: If True, parse and validate but do not write any output.
        overwrite: If True, overwrite the output file if it exists.
    """
    snapshots_path = Path(snapshots_csv)
    if not snapshots_path.exists():
        logger.error("Snapshots CSV not found: %s", snapshots_path)
        raise FileNotFoundError(snapshots_path)

    df_snapshots = pd.read_csv(snapshots_path)
    logger.info("Loaded %d snapshots from %s", len(df_snapshots), snapshots_path)

    # Build matches from snapshots
    matches_df = build_matches_from_snapshots(df_snapshots)

    # Enforce canonical schema for matches
    matches_df = SchemaManager.patch_schema(matches_df, "matches")

    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", output_path)
        return

    if dry_run:
        logger.info(
            "Dry-run mode; would write %d matches to %s", len(matches_df), output_path
        )
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matches_df.to_csv(output_path, index=False)
        logger.info("Matches written to %s", output_path)


if __name__ == "__main__":
    main()
