"""
Simple utilities for row/column filtering.
"""

import pandas as pd
from typing import List


def filter_by_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Return DataFrame with only specified columns (ignoring missing).
    """
    return df[[col for col in columns if col in df.columns]]
