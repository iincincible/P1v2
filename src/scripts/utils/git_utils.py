"""
Utilities for interacting with Git for reproducibility.
"""

import subprocess

from .logger import log_warning


def get_git_hash() -> str | None:
    """
    Get the current short git hash.

    :return: The 7-character git hash as a string, or None if git is not available
             or the project is not a git repository.
    """
    try:
        # The 'capture_output=True' and 'text=True' arguments require Python 3.7+
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,  # This will raise CalledProcessError if the command fails
            encoding="utf-8",
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        log_warning(f"Could not get git hash: {e}")
        return None
