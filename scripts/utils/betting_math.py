import pandas as pd

def compute_ev(prob: float, odds: float) -> float:
    """
    Expected value = (probability of win * payout) - 1
    """
    return (prob * odds) - 1

def compute_kelly_stake(prob: pd.Series, odds: pd.Series) -> pd.Series:
    """
    Vectorized Kelly stake:
    kelly_fraction = ((b * p) - q) / b, where:
        - b = odds - 1
        - p = win probability
        - q = 1 - p
    """
    b = odds - 1
    q = 1 - prob
    edge = (b * prob - q) / b
    return edge.clip(lower=0)
