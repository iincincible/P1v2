"""
Snapshot parsing utilities.
Provides both functional and class-based interfaces.
"""

import pandas as pd


def parse_file(file_path: str) -> pd.DataFrame:
    """
    Read a snapshot CSV file into a DataFrame.
    """
    return pd.read_csv(file_path)


def should_parse_file(file_path: str) -> bool:
    """
    Decide whether a given file should be parsed.
    Current rule: only parse .csv files.
    """
    return file_path.lower().endswith(".csv")


class SnapshotParser:
    """
    Class-based wrapper for snapshot parsing logic.
    """

    def __init__(self, mode: str):
        self.mode = mode

    def parse_file(self, file_path: str) -> pd.DataFrame:
        """
        Delegate to functional parse_file.
        """
        return parse_file(file_path)

    def should_parse_file(self, file_path: str) -> bool:
        """
        Delegate to functional should_parse_file.
        """
        return should_parse_file(file_path)
