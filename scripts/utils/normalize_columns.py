import pandas as pd

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names for simulation and value bet filtering.
    Ensures presence of: predicted_prob, expected_value, odds.
    """
    renamed = df.copy()

    # Fallback renaming map for legacy or alternate column names
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

    for old, new in rename_map.items():
        if old in renamed.columns and new not in renamed.columns:
            renamed[new] = renamed[old]

    # Final check
    required = ["expected_value", "odds", "predicted_prob"]
    missing = [col for col in required if col not in renamed.columns]
    if missing:
        raise ValueError(f"❌ Cannot compute or find required columns: {missing}")

    return renamed
