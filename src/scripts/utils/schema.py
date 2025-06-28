"""
Column normalization and schema enforcement.
"""

import pandas as pd
from typing import Optional, Dict

COLUMN_ALIASES: Dict[str, str] = {
    "playerOne": "player_1",
    "playerTwo": "player_2",
    "winnerName": "winner",
    # ...add all necessary mappings
}

SCHEMAS: Dict[str, list] = {
    "features": [
        "match_id",
        "player_1",
        "player_2",
        "implied_prob_1",
        "implied_prob_2",
        "implied_prob_diff",
        "odds_margin",
    ],
    "value_bets": [
        "match_id",
        "player_1",
        "player_2",
        "odds",
        "predicted_prob",
        "expected_value",
        "kelly_fraction",
        "confidence_score",
    ],
    "matches_with_ids": [
        "match_id",
        "player_1",
        "player_2",
        "selection_id_1",
        "selection_id_2",
    ],
    "merged_matches": [
        "match_id",
        "player_1",
        "player_2",
        "selection_id_1",
        "selection_id_2",
        "final_ltp",
    ],
    "predictions": ["match_id", "player_1", "player_2", "predicted_prob"],
    "simulations": ["match_id", "bankroll", "kelly_fraction", "winner", "odds"],
}


def normalize_columns(
    df: pd.DataFrame, aliases: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Standardize DataFrame columns to pipeline conventions.
    """
    if aliases is None:
        aliases = COLUMN_ALIASES
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    return df


def enforce_schema(df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    """
    Ensure DataFrame has all columns for the schema. Missing columns are added with NaN.
    """
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}")
    cols = SCHEMAS[schema_name]
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA
    return df[cols]


def patch_winner_column(df: pd.DataFrame, winner_col: str = "winner") -> pd.DataFrame:
    """
    Patch winner column to be 0/1 and fill missing with 0.
    """
    df = df.copy()
    if winner_col in df.columns:
        df[winner_col] = df[winner_col].fillna(0).astype(int)
    return df
