import pandas as pd
from scripts.utils.logger import log_error

RENAME_COLS = {
    "prob_1": "implied_prob_1",
    "prob_2": "implied_prob_2",
    "margin": "odds_margin",
    "prob_diff": "implied_diff",
    "odds1": "odds_player_1",
    "odds2": "odds_player_2",
}

REQUIRED_COLS = [
    "market_id", "player_1", "player_2", "odds_player_1", "odds_player_2",
    "match_id", "actual_winner", "winner_name", "loser_name",
    "match_date", "selection_id_1", "selection_id_2"
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.rename(columns=RENAME_COLS)

    if "odds" not in renamed.columns and "odds_player_2" in renamed.columns:
        renamed["odds"] = renamed["odds_player_2"]
    if "odds_2" not in renamed.columns and "odds_player_1" in renamed.columns:
        renamed["odds_2"] = renamed["odds_player_1"]

    if "implied_prob" not in renamed.columns and "odds" in renamed.columns:
        renamed["implied_prob"] = 1 / renamed["odds"]
    if "implied_prob_2" not in renamed.columns and "odds_player_2" in renamed.columns:
        renamed["implied_prob_2"] = 1 / renamed["odds_player_2"]
    if "implied_prob_1" not in renamed.columns and "implied_prob_2" in renamed.columns:
        renamed["implied_prob_1"] = 1 - renamed["implied_prob_2"]
    if "implied_diff" not in renamed.columns and {"implied_prob_1", "implied_prob_2"}.issubset(renamed.columns):
        renamed["implied_diff"] = renamed["implied_prob_1"] - renamed["implied_prob_2"]

    missing = [col for col in REQUIRED_COLS if col not in renamed.columns]
    if missing:
        log_error(f"❌ Missing required columns: {missing}. Available: {list(renamed.columns)}")
        raise ValueError(f"Missing required columns: {missing}")

    return renamed


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a binary 'winner' column to the DataFrame if it's missing.

    The logic assumes:
      - 'player_1' is the predicted player
      - 'actual_winner' contains the true winner name

    The column is computed as:
        winner = int(actual_winner.lower().strip() == player_1.lower().strip())

    If 'winner' already exists, the function leaves it unchanged.

    Parameters:
        df (pd.DataFrame): A DataFrame containing at least 'player_1' and 'actual_winner' columns

    Returns:
        pd.DataFrame: The original DataFrame with a 'winner' column added if needed
    """
    if "winner" not in df.columns:
        if "actual_winner" in df.columns and "player_1" in df.columns:
            df["winner"] = (
                df["actual_winner"].str.strip().str.lower() ==
                df["player_1"].str.strip().str.lower()
            ).astype(int)
    return df
