"""
Statistical utility functions.
"""

import pandas as pd


def compute_roi(
    df: pd.DataFrame, profit_col: str = "profit", stake_col: str = "stake"
) -> float:
    """
    Compute return on investment.
    """
    total_profit = df[profit_col].sum()
    total_staked = df[stake_col].sum()
    if total_staked == 0:
        return 0.0
    return total_profit / total_staked
