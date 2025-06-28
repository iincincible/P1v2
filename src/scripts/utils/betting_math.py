"""
Betting-related mathematical utilities.
"""

import pandas as pd


def add_ev_and_kelly(
    df: pd.DataFrame,
    prob_col: str = "predicted_prob",
    odds_col: str = "odds",
    min_prob: float = 1e-8,
    fillna: bool = True,
) -> pd.DataFrame:
    """
    Add expected value (EV) and Kelly fraction columns to the DataFrame.
    Assumes that higher prob_col means higher likelihood of win for that bet.
    """
    df = df.copy()
    prob = df[prob_col].clip(lower=min_prob, upper=1 - min_prob)
    odds = df[odds_col]
    df["expected_value"] = prob * (odds - 1) - (1 - prob)
    df["kelly_fraction"] = (prob * (odds - 1) - (1 - prob)) / (odds - 1)
    if fillna:
        df.fillna(0, inplace=True)
    return df
