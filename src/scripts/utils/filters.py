import pandas as pd

def filter_value_bets(df: pd.DataFrame, ev_threshold: float, max_odds: float, max_margin: float) -> pd.DataFrame:
    """
    Filters a DataFrame of predictions based on EV, odds, and margin.
    Returns a filtered copy of the DataFrame.
    """
    return df[
        (df["expected_value"] >= ev_threshold) &
        (df["odds"] <= max_odds) &
        (df["odds_margin"] <= max_margin)
    ].copy()
