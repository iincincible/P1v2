from pathlib import Path
import os
import argparse
import pandas as pd

from scripts.utils.logger import log_error


def add_common_flags(parser: argparse.ArgumentParser):
    """
    Add shared CLI flags for overwrite protection and dry-run simulation.
    """
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--dry_run", action="store_true", help="Only simulate the steps without writing output")


def should_run(output_path: Path, overwrite: bool, dry_run: bool) -> bool:
    """
    Decide whether to proceed with generating output at the given path.
    """
    if output_path.exists():
        if not overwrite:
            if dry_run:
                return True
            log_error(f"⚠️ Output exists: {output_path} — use --overwrite to replace.")
            return False
        if dry_run:
            return True

    return True


def assert_file_exists(path: Path | str, name: str = "file"):
    """
    Raise an error if a file or directory does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"❌ {name} not found: {path}")


def assert_columns_exist(df: pd.DataFrame, cols: list[str], context: str = ""):
    """
    Raise an error if required columns are missing from a DataFrame.
    """
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns in {context}: {missing}")
