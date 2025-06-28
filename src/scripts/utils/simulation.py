"""
Bankroll simulation utilities.
"""

import pandas as pd


def simulate_bankroll(
    bets: pd.DataFrame,
    initial_bankroll: float = 1000.0,
    kelly_col: str = "kelly_fraction",
    odds_col: str = "odds",
    winner_col: str = "winner",
) -> pd.Series:
    """
    Simulate cumulative bankroll over a sequence of bets.
    """
    bankroll = [initial_bankroll]
    for i, row in bets.iterrows():
        prev = bankroll[-1]
        stake = prev * row.get(kelly_col, 0)
        won = row.get(winner_col, 0)
        odds = row.get(odds_col, 1.0)
        pnl = stake * (odds - 1) * won - stake * (1 - won)
        bankroll.append(prev + pnl)
    return pd.Series(bankroll[1:], index=bets.index)
