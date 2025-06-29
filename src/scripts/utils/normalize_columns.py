"""
Normalize DataFrame column names and enforce canonical schema.
"""

from typing import List
import pandas as pd

CANONICAL_REQUIRED_COLUMNS: List[str] = [
    # Example canonical columns; update as needed
    "winner",
    "loser",
    "score",
    "round",
    "date",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names: strip whitespace, lowercase, replace spaces with underscores.
    """
    df = df.copy()
    normalized = {col: col.strip().lower().replace(" ", "_") for col in df.columns}
    df.rename(columns=normalized, inplace=True)
    return df


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename legacy winner column (e.g., 'w') to 'winner'.
    """
    df = df.copy()
    if "w" in df.columns and "winner" not in df.columns:
        df.rename(columns={"w": "winner"}, inplace=True)
    return df


def assert_required_columns(
    df: pd.DataFrame,
    required: List[str] = CANONICAL_REQUIRED_COLUMNS,
    context: str = "",
) -> None:
    """
    Ensure that the DataFrame contains all required canonical columns.
    """
    missing = set(required) - set(df.columns)
    if missing:
        prefix = f"{context}: " if context else ""
        raise ValueError(f"{prefix}Missing required columns: {sorted(missing)}")
