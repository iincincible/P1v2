import pandas as pd

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names for simulation and value bet filtering.
    Ensures presence of: predicted_prob, expected_value, odds.
    Also patches implied_prob_diff if needed.
    """
    renamed = df.copy()

    rename_map = {
        "ev": "expected_value",
        "prob": "predicted_prob",
        "pred_prob": "predicted_prob",
        "pred_prob_player_1": "predicted_prob",
        "odds_player_1": "odds",
        "odds_player_2": "odds_2",
        "implied_prob_1": "implied_prob",
        "confidence_score": "confidence",
    }

    # Only rename if target doesn't already exist
    for old, new in rename_map.items():
        if old in renamed.columns and new not in renamed.columns:
            renamed[new] = renamed[old]

    # Patch implied_prob_diff if missing
    if "implied_prob_diff" not in renamed.columns:
        if "implied_prob_1" in renamed.columns and "implied_prob_2" in renamed.columns:
            renamed["implied_prob_diff"] = renamed["implied_prob_1"] - renamed["implied_prob_2"]

    required = ["expected_value", "odds", "predicted_prob"]
    missing = [col for col in required if col not in renamed.columns]
    if missing:
        raise ValueError(f"❌ Missing required columns: {missing}. Available: {list(renamed.columns)}")

    return renamed
