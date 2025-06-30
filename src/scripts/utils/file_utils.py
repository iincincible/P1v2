"""
Utilities for robust file IO operations.
"""

import glob
from pathlib import Path

import pandas as pd

from .logger import log_info, log_warning


def load_dataframes(file_glob: str) -> pd.DataFrame:
    """
    Load and concatenate multiple CSVs from a glob pattern.

    :param file_glob: Glob pattern for input CSV files.
    :return: A single concatenated DataFrame.
    """
    files = glob.glob(file_glob)
    if not files:
        raise FileNotFoundError(f"No files found matching glob pattern: {file_glob}")

    log_info(f"Found {len(files)} files matching '{file_glob}'.")
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception as e:
            log_warning(f"Skipping file {f} due to error: {e}")

    if not dfs:
        raise ValueError("No valid DataFrames were loaded.")

    combined_df = pd.concat(dfs, ignore_index=True)
    log_info(
        f"Successfully loaded and combined {len(dfs)} files into a DataFrame with {len(combined_df)} rows."
    )
    return combined_df


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
