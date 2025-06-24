"""
Test that all pipeline steps produce canonical columns as documented in the data contract.
"""

import pandas as pd
from scripts.utils.normalize_columns import (
    normalize_columns,
    CANONICAL_REQUIRED_COLUMNS,
    assert_required_columns,
)


def test_column_normalization():
    raw = pd.DataFrame(
        {
            "runner_1": ["Alice"],
            "runner_2": ["Bob"],
            "prob": [0.65],
            "odds_player_1": [2.1],
            "ev": [0.36],
            "actual_winner": ["Alice"],
        }
    )
    norm = normalize_columns(raw)
    for col in ["player_1", "player_2", "predicted_prob", "odds", "expected_value"]:
        assert col in norm.columns, f"{col} missing after normalization"
    from scripts.utils.normalize_columns import patch_winner_column

    norm = patch_winner_column(norm)
    assert "winner" in norm.columns
    assert_required_columns(norm, CANONICAL_REQUIRED_COLUMNS)
