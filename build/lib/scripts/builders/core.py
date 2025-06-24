import logging
from typing import Optional

import pandas as pd

from scripts.utils.logger import log_info
from scripts.utils.matching import (
    apply_alias_map,
    fuzzy_match_players,
    load_alias_map,
    match_snapshots_to_results,
)

# Refactor: Add logging config
logging.basicConfig(level=logging.INFO)


def build_matches_from_snapshots(
    snapshot_csv: str,
    sackmann_csv: Optional[str] = None,
    alias_csv: Optional[str] = None,
    snapshot_only: bool = False,
    fuzzy_match: bool = False,
) -> pd.DataFrame:
    """
    Builds a clean match dataset from Betfair snapshot data.
    """
    log_info(f"📄 Reading snapshots from: {snapshot_csv}")
    df = pd.read_csv(snapshot_csv)
    df = df.dropna(subset=["runner_1", "runner_2"]).copy()

    df["match_key"] = (
        df["market_time"].astype(str) + "_" + df["runner_1"] + "_" + df["runner_2"]
    )
    df = df.drop_duplicates(subset=["match_key", "selection_id", "timestamp"])

    grouped = (
        df.groupby("match_key")
        .agg(
            {
                "market_time": "first",
                "market_id": "first",
                "runner_1": "first",
                "runner_2": "first",
                "selection_id": list,
                "ltp": list,
                "timestamp": list,
                "runner_name": list,
            }
        )
        .reset_index(drop=True)
    )

    grouped["match_id"] = grouped.apply(
        lambda row: f"{row['market_id']}_{row['runner_1']}_{row['runner_2']}", axis=1
    )

    alias_map = load_alias_map(alias_csv) if alias_csv else {}
    if alias_map:
        grouped = apply_alias_map(grouped, alias_csv)

    if fuzzy_match:
        grouped = fuzzy_match_players(grouped)

    if not snapshot_only and sackmann_csv:
        grouped = match_snapshots_to_results(
            grouped, sackmann_csv, alias_map=alias_map, fuzzy=fuzzy_match
        )

    grouped["player_1"] = grouped["runner_1"]
    grouped["player_2"] = grouped["runner_2"]

    # Order canonical columns first
    canonical_order = [
        "player_1",
        "player_2",
        "match_id",
        "market_id",
        "market_time",
        "selection_id",
        "ltp",
        "timestamp",
        "runner_name",
    ]
    others = [c for c in grouped.columns if c not in canonical_order]
    grouped = grouped[canonical_order + others]

    # Refactor: Enforce canonical columns if output is for pipeline
    # Not enforced here, but enforced in build_matches_generic.py
    return grouped
