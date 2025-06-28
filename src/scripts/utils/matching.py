"""
Utilities for fuzzy and exact string matching.
"""

from typing import Optional, List
import difflib


def fuzzy_match(query: str, choices: List[str], cutoff: float = 0.8) -> Optional[str]:
    """
    Fuzzy match a string to a list, returning best or None.
    """
    results = difflib.get_close_matches(query, choices, n=1, cutoff=cutoff)
    return results[0] if results else None
