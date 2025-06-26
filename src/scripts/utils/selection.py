import pandas as pd
from collections import defaultdict


def build_market_runner_map(df_snaps):
    """
    Build mapping of (market_id, player_name) to selection_id.
    """
    market_map = defaultdict(dict)
    for _, row in df_snaps.iterrows():
        market = row.get("market_id")
        selection_id = row.get("selection_id")
        player = row.get("runner_name") or row.get("player") or row.get("player_name")
        if pd.notnull(market) and pd.notnull(player):
            market_map[market][player] = selection_id
    return market_map


def match_player_to_selection_id(market_map, market_id, player_name):
    if market_id in market_map and player_name in market_map[market_id]:
        return market_map[market_id][player_name]
    # Fallback: try case-insensitive
    candidates = {k.lower(): v for k, v in market_map.get(market_id, {}).items()}
    return candidates.get(str(player_name).lower())
