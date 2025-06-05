def compute_ev(prob: float, odds: float) -> float:
    """
    Compute expected value (EV) of a bet.

    EV = (P * (O - 1)) - (1 - P)

    Where:
    - P is the predicted probability of winning
    - O is the decimal odds offered
    """
    return (prob * (odds - 1)) - (1 - prob)


def compute_kelly_stake(prob: float, odds: float, bankroll: float = 1000.0) -> float:
    """
    Compute stake size using the Kelly Criterion (fractional).

    stake = bankroll * ((bp - q) / b)
    Where:
    - b = odds - 1
    - p = probability of winning
    - q = 1 - p
    - stake is capped at bankroll

    Returns 0 if the Kelly fraction is non-positive.
    """
    b = odds - 1
    q = 1 - prob
    kelly_fraction = ((b * prob) - q) / b if b > 0 else 0
    return max(0, kelly_fraction * bankroll)
