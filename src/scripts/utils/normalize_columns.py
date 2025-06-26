import pandas as pd
from scripts.utils.logger import log_info

CANONICAL_COLS = {
    "player1": "player_1",
    "player2": "player_2",
    "team1": "player_1",
    "team2": "player_2",
    "matchwinner": "winner",
    "result": "winner",
    "prob": "predicted_prob",
    "probability": "predicted_prob",
}


def normalize_and_patch_canonical_columns(df, context=None):
    df = df.copy()
    # Rename columns to canonical names if necessary
    rename_map = {
        col: CANONICAL_COLS[col.lower()]
        for col in df.columns
        if col.lower() in CANONICAL_COLS
    }
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
        log_info(
            f"Renamed columns to canonical names: {rename_map} (context: {context})"
        )
    return patch_winner_column(df)


def patch_winner_column(df):
    # Winner column: must be 1 (player_1 wins), 0 (player_2 wins), or NaN
    if "winner" in df.columns:
        df["winner"] = df["winner"].map(
            lambda x: (
                1
                if x in [1, "1", "A", "player_1"]
                else 0 if x in [0, "0", "B", "player_2"] else pd.NA
            )
        )
    return df


def enforce_canonical_columns(df, context=None):
    # Minimal check; could be extended
    for must_col in ["player_1", "player_2"]:
        if must_col not in df.columns:
            raise ValueError(
                f"Missing required column: {must_col} (context: {context})"
            )
    return df
