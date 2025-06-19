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

def add_ev_and_kelly(df: pd.DataFrame, prob_col="predicted_prob", odds_col="odds") -> pd.DataFrame:
    """
    Adds expected_value and kelly_stake columns to a DataFrame using the specified prob and odds columns.
    """
    df["expected_value"] = compute_ev(df[prob_col], df[odds_col])
    df["kelly_stake"] = compute_kelly_stake(df[prob_col], df[odds_col])
    return df

def compute_kelly_stake_capped(prob: float, odds: float, bankroll: float = 1.0, cap: float = 0.05) -> float:
    """
    Computes the Kelly stake (fraction of bankroll), capped at a maximum %.
    """
    b = odds - 1
    q = 1 - prob
    if b <= 0:
        return 0
    edge = (b * prob - q) / b
    stake = edge * bankroll
    return max(0, min(stake, bankroll * cap))
