"""
Common CLI utilities for file and DataFrame handling.
"""

import os


def assert_file_exists(path: str, description: str) -> None:
    """
    Ensure that the given file path exists, otherwise raise FileNotFoundError.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{description} not found: {path}")


def should_run(path: str, overwrite: bool = False, dry_run: bool = False) -> bool:
    """
    Determine if an operation should actually run.
    - If dry_run is True, log and return False.
    - If overwrite is True or the target does not exist, return True.
    - Otherwise, skip by returning False.
    """
    if dry_run:
        from scripts.utils.logger import log_dryrun

        log_dryrun(f"Skipping actual run for {path}")
        return False
    if overwrite or not os.path.exists(path):
        return True
    return False


def assert_columns_exist(df, columns, context: str = "") -> None:
    """
    Check that all specified columns exist in the DataFrame; raise ValueError otherwise.
    """
    missing = set(columns) - set(df.columns)
    if missing:
        prefix = f"{context}: " if context else ""
        raise ValueError(f"{prefix}Missing columns: {sorted(missing)}")


# Retain deprecated decorator for backward compatibility
def cli_entrypoint(func):
    """
    Decorator marking a function as a CLI entrypoint (legacy).
    """

    def wrapper():
        return func()

    return wrapper
