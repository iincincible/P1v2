"""
Match player names in matches to Betfair selection IDs using parsed snapshots.
"""

import pandas as pd
from pathlib import Path

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)

logger = getLogger(__name__)


@guarded_run
def main(
    merged_csv: str,
    snapshots_csv: str,
    output_csv: str,
    max_missing_frac: float = 0.1,
    drop_missing_rows: bool = False,
    ignore_missing: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
):
    """
    Assign selection IDs to matches based on snapshot data.
    """
    in_matches = Path(merged_csv)
    in_snaps = Path(snapshots_csv)
    if not in_matches.exists():
        logger.error("Merged CSV not found: %s", in_matches)
        raise FileNotFoundError(in_matches)
    if not in_snaps.exists():
        logger.error("Snapshots CSV not found: %s", in_snaps)
        raise FileNotFoundError(in_snaps)

    df_matches = pd.read_csv(in_matches)
    logger.info("Loaded %d matches from %s", len(df_matches), in_matches)
    df_snaps = pd.read_csv(in_snaps)
    logger.info("Loaded %d snapshots from %s", len(df_snaps), in_snaps)

    market_map = build_market_runner_map(df_snaps)

    # Map player_1 and player_2 to IDs
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

    # Check missing IDs
    total = len(df_matches)
    miss1 = df_matches["selection_id_1"].isna().sum()
    miss2 = df_matches["selection_id_2"].isna().sum()
    frac1 = miss1 / total if total else 0
    frac2 = miss2 / total if total else 0
    if miss1 or miss2:
        logger.warning(
            "Unmatched IDs 1: %d (%.1%%), IDs 2: %d (%.1%%)", miss1, frac1, miss2, frac2
        )
        if (
            frac1 > max_missing_frac or frac2 > max_missing_frac
        ) and not ignore_missing:
            logger.error(
                "Too many unmatched IDs (> %.0%%). Use --ignore_missing to override.",
                max_missing_frac,
            )
            return
    if drop_missing_rows:
        before = total
        df_matches = df_matches.dropna(subset=["selection_id_1", "selection_id_2"])
        logger.info("Dropped %d rows with missing IDs", before - len(df_matches))

    SchemaManager.patch_schema(df_matches, "matches_with_ids")

    out = Path(output_csv)
    if out.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out)
        return
    if dry_run:
        logger.info("Dry-run: would write %d rows to %s", len(df_matches), out)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        df_matches.to_csv(out, index=False)
        logger.info("Saved selection IDs to %s", out)


if __name__ == "__main__":
    main()
