"""
Parsers for raw snapshot files into DataFrames.
"""

import pandas as pd


def parse_snapshot_file(filepath: str) -> pd.DataFrame:
    """
    Parse a CSV snapshot into a standardized DataFrame.
    """
    df = pd.read_csv(filepath)
    # Add normalization as needed
    return df
