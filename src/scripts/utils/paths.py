"""
Helpers for consistent pipeline paths.
"""

from pathlib import Path


def get_output_dir(base_dir: str, label: str) -> Path:
    """
    Generate a standard output directory for a label.
    """
    return Path(base_dir) / label
