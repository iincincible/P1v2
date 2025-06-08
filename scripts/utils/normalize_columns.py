import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize common column aliases to consistent internal naming.
    For example, renames 'prob' → 'predicted_prob', 'model_prob' → 'predicted_prob'.
    """
    rename_map = {
        "prob": "predicted_prob",
        "model_prob": "predicted_prob",
        "ev": "expected_value",
        "value": "expected_value",
    }

    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure a binary 'winner' column exists and is valid (0 or 1 only).
    If missing, infers from 'actual_winner' vs. 'player_1'.
    """
    if "winner" in df.columns and set(df["winner"].dropna().unique()).issubset({0, 1}):
        return df

    if "actual_winner" in df.columns and "player_1" in df.columns:
        df["winner"] = (df["actual_winner"] == df["player_1"]).astype(int)
    elif "expected_value" in df.columns:
        df["winner"] = (df["expected_value"] > 0).astype(int)
    else:
        raise ValueError("❌ Cannot patch winner column — missing actual_winner or expected_value")

    return df
