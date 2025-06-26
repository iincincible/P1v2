"""
Merge the final LTP (last traded price) from snapshot data into the matches DataFrame.
"""

import pandas as pd
from pathlib import Path

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)


@guarded_run
def main(
    matches_csv: str,
    snapshots_csv: str,
    output_csv: str,
    dry_run: bool = False,
    overwrite: bool = False,
):
    """
    Args:
        matches_csv: Path to the CSV with base matches data (from build stage).
        snapshots_csv: Path to CSV of LTP snapshots (from snapshot parsing stage).
        output_csv: Path to write the merged matches CSV.
        dry_run: If True, simulate without writing files.
        overwrite: If True, overwrite existing output file.
    """
    matches_path = Path(matches_csv)
    snaps_path = Path(snapshots_csv)
    if not matches_path.exists():
        logger.error("Matches CSV not found: %s", matches_path)
        raise FileNotFoundError(matches_path)
    if not snaps_path.exists():
        logger.error("Snapshots CSV not found: %s", snaps_path)
        raise FileNotFoundError(snaps_path)

    # Load data
    df_matches = pd.read_csv(matches_path)
    logger.info("Loaded %d matches from %s", len(df_matches), matches_path)
    df_snaps = pd.read_csv(snaps_path)
    logger.info("Loaded %d snapshot rows from %s", len(df_snaps), snaps_path)

    # Determine final LTP per match_id and selection
    final_snaps = (
        df_snaps.sort_values(["match_id", "selection_id", "timestamp"])
        .groupby(["match_id", "selection_id"], as_index=False)
        .last()[["match_id", "selection_id", "ltp"]]
    )
    logger.debug(
        "Computed final LTP for %d (match_id, selection_id) pairs", len(final_snaps)
    )

    # Merge into matches
    df_merged = df_matches.merge(
        final_snaps,
        on=["match_id", "selection_id"],
        how="left",
        suffixes=("", "_final"),
    )
    # If no final LTP found, ltp_final will be NaN
    df_merged.rename(columns={"ltp_final": "final_ltp"}, inplace=True)

    # Enforce schema on merged matches
    df_out = SchemaManager.patch_schema(df_merged, "merged_matches")

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out_path)
        return

    if dry_run:
        logger.info(
            "Dry-run: would write %d merged matches to %s", len(df_out), out_path
        )
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        logger.info("Merged matches written to %s", out_path)


if __name__ == "__main__":
    main()
