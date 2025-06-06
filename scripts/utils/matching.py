import pandas as pd
from rapidfuzz import fuzz
from pathlib import Path

def normalize_name(name: str) -> str:
    """
    Lowercase, strip punctuation, whitespace and normalize for matching.
    """
    return str(name).lower().replace(".", "").replace("-", " ").strip()

def load_alias_map(alias_csv: str) -> dict:
    """
    Loads a CSV of alias,full_name pairs and returns a mapping dictionary.
    """
    if alias_csv and Path(alias_csv).exists():
        alias_df = pd.read_csv(alias_csv)
        alias_df = alias_df.dropna(subset=["alias", "full_name"])
        return dict(zip(alias_df["alias"].str.strip(), alias_df["full_name"].str.strip()))
    return {}

def build_roster_map(sack_df: pd.DataFrame) -> dict:
    """
    Builds a normalized name → original name map from Sackmann match results.
    """
    roster = pd.Series(pd.concat([sack_df["winner_name"], sack_df["loser_name"]], ignore_index=True).unique())
    roster_clean = roster.map(normalize_name).tolist()
    return dict(zip(roster_clean, roster))

def resolve_player(betfair_name: str, roster_map: dict, alias_map: dict, use_fuzzy: bool = True) -> str | None:
    """
    Attempts to resolve a Betfair player name to a canonical full name using:
    1. Alias match
    2. Exact substring match
    3. Fuzzy token sort match (if enabled)

    Returns the full name if found, otherwise None.
    """
    if betfair_name in alias_map:
        return alias_map[betfair_name]

    clean_bf = normalize_name(betfair_name)

    # Exact partial match
    for rc, full_name in roster_map.items():
        if rc in clean_bf or clean_bf in rc:
            return full_name

    # Fuzzy fallback
    if use_fuzzy:
        best_match, best_score = None, 0
        for rc, full_name in roster_map.items():
            score = fuzz.token_sort_ratio(clean_bf, rc)
            if score > best_score:
                best_match, best_score = full_name, score
        return best_match if best_score >= 80 else None

    return None
