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
    """
    Renames all columns in the input DataFrame to canonical pipeline columns.

    **Canonical columns:**
      - player_1, player_2, odds, predicted_prob, expected_value, winner
      - (plus any others, as documented in the pipeline contract)
    """
    df = df.rename(
        columns={k: v for k, v in CANONICAL_RENAME_MAP.items() if k in df.columns}
    )
    return df


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    if "winner" in df.columns and set(df["winner"].dropna().unique()).issubset({0, 1}):
        return df
    if "actual_winner" in df.columns and "player_1" in df.columns:
        df["winner"] = (df["actual_winner"] == df["player_1"]).astype(int)
    elif "expected_value" in df.columns:
        df["winner"] = (df["expected_value"] > 0).astype(int)
    else:
        raise ValueError(
            "❌ Cannot patch winner column — missing actual_winner or expected_value"
        )
    return df


def prepare_value_bets_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies normalization and value-bet fields (EV, Kelly, winner) to the input DataFrame.
    Ensures canonical columns for downstream scripts.
    """
    from scripts.utils.betting_math import add_ev_and_kelly

    df = normalize_columns(df)
    df = add_ev_and_kelly(df)
    df = patch_winner_column(df)
    return df


def assert_required_columns(
    df: pd.DataFrame, required=CANONICAL_REQUIRED_COLUMNS, context=""
) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns in {context}: {missing}")


def enforce_canonical_columns(
    df: pd.DataFrame, required=CANONICAL_REQUIRED_COLUMNS, context=""
):
    """
    Enforces canonical columns after any DataFrame output. Raises ValueError if missing.
    """
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"❌ Missing required columns after output in {context}: {missing}"
        )
    return True
