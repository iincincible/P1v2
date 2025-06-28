"""
Utilities for robust file IO operations.
"""

import pandas as pd
from pathlib import Path


def read_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Robust CSV reader with existence check.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return pd.read_csv(path, **kwargs)


def write_csv(
    df: pd.DataFrame, filepath: str, overwrite: bool = False, **kwargs
) -> None:
    """
    Robust CSV writer with overwrite protection.
    """
    path = Path(filepath)
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {filepath} (use overwrite=True to force)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, **kwargs)
