# tests/test_utils.py

def test_pytest_works():
    """Sanity check: Pytest should find and run this test."""
    assert 1 + 1 == 2

import pandas as pd
from scripts.utils.normalize_columns import patch_winner_column

def test_patch_winner_column():
    """patch_winner_column should create a 'winner' column with 1 for player_1 win and 0 otherwise."""
    df = pd.DataFrame({
        "player_1": ["Serena", "Venus", "Novak"],
        "player_2": ["Venus", "Serena", "Rafa"],
        "actual_winner": ["Serena", "Serena", "Rafa"]
    })
    result = patch_winner_column(df)
    assert "winner" in result.columns
    # Serena wins (player_1), then Serena wins (not player_1), then Rafa wins (not player_1)
    assert list(result["winner"]) == [1, 0, 0]
