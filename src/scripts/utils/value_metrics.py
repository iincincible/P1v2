"""
Metrics and computations for value bets.
"""

import pandas as pd


def compute_value_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add value-bet-related columns (EV, Kelly, etc.).
    """
    df = df.copy()
    if "predicted_prob" in df.columns and "odds" in df.columns:
        df["expected_value"] = df["predicted_prob"] * (df["odds"] - 1) - (
            1 - df["predicted_prob"]
        )
        df["kelly_fraction"] = (
            df["predicted_prob"] * (df["odds"] - 1) - (1 - df["predicted_prob"])
        ) / (df["odds"] - 1)
        df["kelly_fraction"] = df["kelly_fraction"].fillna(0)
    return df
