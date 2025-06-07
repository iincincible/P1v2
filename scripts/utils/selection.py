from collections import defaultdict
from difflib import get_close_matches

def build_market_runner_map(snapshots_df):
    """
    Builds a map: market_id → {runner_name_clean → selection_id}
    """
    market_runner_map = defaultdict(dict)
    for _, row in snapshots_df.iterrows():
        market_id = str(row["market_id"])
        runner_name = str(row["runner_name"]).lower().strip()
        selection_id = row["selection_id"]
        market_runner_map[market_id][runner_name] = selection_id
    return market_runner_map

def match_player_to_selection_id(market_runner_map, market_id, player_name, cutoff=0.8):
    """
    Fuzzy matches a player_name to a runner name for a given market.
    Returns the best matching selection_id, or None.
    """
    player_clean = str(player_name).lower().strip()
    candidates = list(market_runner_map.get(str(market_id), {}).keys())
    match = get_close_matches(player_clean, candidates, n=1, cutoff=cutoff)
    if match:
        return market_runner_map[str(market_id)].get(match[0])
    return None
