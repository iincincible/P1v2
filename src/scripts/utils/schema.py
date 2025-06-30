"""
Column normalization and schema enforcement.
"""

import re
from typing import Dict

import pandas as pd

COLUMN_ALIASES: Dict[str, str] = {
    "playerOne": "player_1",
    "playerTwo": "player_2",
    "winnerName": "winner",
    "prob": "predicted_prob",
    "ev": "expected_value",
    "actual_winner": "winner",
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
        "winner",
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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame columns to pipeline conventions by cleaning names,
    applying aliases, and reordering.
    """
    df = df.copy()

    # Basic cleanup: strip, lowercase, underscores
    cleaned_cols = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.columns = cleaned_cols

    # Runner -> Player mapping via regex
    runner_map = {
        col: f"player_{m.group(1)}"
        for col in df.columns
        if (m := re.match(r"runner_(\d+)$", col))
    }
    if runner_map:
        df = df.rename(columns=runner_map)

    # Simple aliases
    existing_aliases = {k: v for k, v in COLUMN_ALIASES.items() if k in df.columns}
    if existing_aliases:
        df = df.rename(columns=existing_aliases)

    # Merge odds_* columns into one 'odds'
    odds_cols = [c for c in df.columns if c.startswith("odds_")]
    if odds_cols:
        df["odds"] = df[odds_cols].bfill(axis=1).iloc[:, 0]
        df = df.drop(columns=odds_cols)

    # Reorder: player_1, player_2, ... then the rest
    player_cols = sorted(
        [c for c in df.columns if c.startswith("player_")],
        key=lambda x: int(x.split("_")[1]),
    )
    other_cols = [c for c in df.columns if c not in player_cols]
    df = df[player_cols + other_cols]

    return df


def enforce_schema(df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    """
    Ensure DataFrame has all columns for the schema.
    Missing columns are added with NaN.
    """
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}")

    # Ensure DataFrame columns are normalized before enforcement
    df = normalize_columns(df)

    cols = SCHEMAS[schema_name]
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA

    return df[cols]


def patch_winner_column(df: pd.DataFrame, winner_col: str = "winner") -> pd.DataFrame:
    """
    Patch winner column to be 0/1 integer type and fill missing with 0.
    """
    df = df.copy()
    if winner_col in df.columns:
        # Ensure winner is numeric before filling NA, then convert to integer
        df[winner_col] = (
            pd.to_numeric(df[winner_col], errors="coerce").fillna(0).astype(int)
        )
    return df
