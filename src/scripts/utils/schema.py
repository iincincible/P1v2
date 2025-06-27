import pandas as pd

CANONICAL_SCHEMAS = {
    "matches": ["match_id", "player_1", "player_2", "scheduled_time", "market_id"],
    "matches_with_ids": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "selection_id_1",
        "selection_id_2",
    ],
    "features": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "ltp_player_1",
        "ltp_player_2",
        "implied_prob_1",
        "implied_prob_2",
        "implied_prob_diff",
        "odds_margin",
    ],
    "predictions": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "implied_prob_1",
        "implied_prob_2",
        "implied_prob_diff",
        "odds_margin",
        "predicted_prob",
    ],
    "value_bets": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "odds",
        "predicted_prob",
        "expected_value",
        "kelly_fraction",
        "confidence_score",
        "winner",
    ],
    "simulations": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "odds",
        "predicted_prob",
        "expected_value",
        "kelly_fraction",
        "winner",
        "bankroll",
    ],
    "merged_matches": [
        "match_id",
        "player_1",
        "player_2",
        "scheduled_time",
        "market_id",
        "selection_id",
        "final_ltp",
    ],
}

COLUMN_ALIASES = {
    "player1": "player_1",
    "player2": "player_2",
    "team1": "player_1",
    "team2": "player_2",
    "matchwinner": "winner",
    "result": "winner",
    "prob": "predicted_prob",
    "probability": "predicted_prob",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        col: COLUMN_ALIASES[col.lower()]
        for col in df.columns
        if col.lower() in COLUMN_ALIASES
    }
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def enforce_schema(df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    expected_cols = CANONICAL_SCHEMAS[schema_name]
    missing = [c for c in expected_cols if c not in df.columns]
    for c in missing:
        df[c] = None
    return df[expected_cols]


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    # Winner must be 1 (player_1 wins), 0 (player_2 wins), or NaN
    if "winner" in df.columns:
        df["winner"] = df["winner"].map(
            lambda x: (
                1
                if x in [1, "1", "A", "player_1"]
                else 0 if x in [0, "0", "B", "player_2"] else pd.NA
            )
        )
    return df
