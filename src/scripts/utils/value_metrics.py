"""
Utility for computing expected value and Kelly fraction for bets.
"""

import pandas as pd
from scripts.utils.logger import getLogger

logger = getLogger(__name__)


def compute_value_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'expected_value' and 'kelly_fraction' columns to the DataFrame.

    Assumes input df has:
      - 'odds': decimal odds for each bet
      - 'probability': estimated win probability

    Returns:
        A new DataFrame with metrics appended.
    """
    df = df.copy()
    # Expected value: EV = p*b - (1-p)
    b = df["odds"] - 1
    p = df["probability"]
    df["expected_value"] = p * b - (1 - p)

    # Kelly fraction: k = (b*p - (1-p)) / b
    df["kelly_fraction"] = (b * p - (1 - p)) / b

    logger.debug("Computed 'expected_value' and 'kelly_fraction' for %d rows", len(df))
    return df
