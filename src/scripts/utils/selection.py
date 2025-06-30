"""
Logic for assigning selection IDs.
"""

from typing import Any, Dict, Optional

import pandas as pd


def build_market_runner_map(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Build a mapping from market_id to player_name -> selection_id.
    """
    mapping = {}
    for _, row in df.iterrows():
        market = row.get("market_id")
        player = row.get("runner_name")
        sel_id = row.get("selection_id")
        if market and player:
            mapping.setdefault(market, {})[player] = sel_id
    return mapping


def match_player_to_selection_id(
    market_map: Dict[str, Dict[str, Any]], market_id: str, player_name: str
) -> Optional[Any]:
    """
    Look up selection_id for a player in a given market.
    """
    return market_map.get(market_id, {}).get(player_name, None)
