# File: src/scripts/utils/normalize_columns.py

import pandas as pd

CANONICAL_RENAME_MAP = {
    "prob": "predicted_prob",
    "model_prob": "predicted_prob",
    "ev": "expected_value",
    "value": "expected_value",
    "odds_player_1": "odds",
    "odds1": "odds",
    "odds2": "odds",
    "Player1": "player_1",
    "Player2": "player_2",
    "runner_1": "player_1",
    "runner_2": "player_2",
    "actualWinner": "actual_winner",
    "winner_name": "actual_winner",
}

CANONICAL_REQUIRED_COLUMNS = [
    "player_1",
    "player_2",
    "odds",
    "predicted_prob",
    "expected_value",
    "winner",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={k: v for k, v in CANONICAL_RENAME_MAP.items() if k in df.columns}
    )


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    # 1) if already 0/1, leave it
    if "winner" in df.columns and set(df["winner"].dropna().unique()).issubset({0, 1}):
        return df

    # 2) if we have actual_winner, must use it
    if "actual_winner" in df.columns and "player_1" in df.columns:
        df["winner"] = (df["actual_winner"] == df["player_1"]).astype(int)
        return df

    # 3) otherwise, we have no legitimate label → error
    raise ValueError(
        "❌ Cannot patch winner column — missing actual_winner in input DataFrame"
    )


def enforce_canonical_columns(
    df: pd.DataFrame, required=CANONICAL_REQUIRED_COLUMNS, context=""
):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"❌ Missing required columns after output in {context}: {missing}"
        )
    return True
