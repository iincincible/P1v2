# tests/utils/test_schema.py

import numpy as np
import pandas as pd

from scripts.utils.schema import enforce_schema, normalize_columns, patch_winner_column


def test_normalize_columns():
    """
    Tests the column normalization logic.
    """
    data = {
        "playerOne": ["A"],
        "playerTwo": ["B"],
        "odds_1": [1.5],
        "actual_winner": [1],
    }
    df = pd.DataFrame(data)

    normalized_df = normalize_columns(df)

    expected_columns = ["player_1", "player_2", "odds", "winner"]
    assert all(col in normalized_df.columns for col in expected_columns)


def test_enforce_schema():
    """
    Tests that enforce_schema adds missing columns.
    """
    data = {"match_id": [1], "player_1": ["A"]}
    df = pd.DataFrame(data)

    # Enforce a schema that has more columns
    value_bets_df = enforce_schema(df, "value_bets")

    assert "predicted_prob" in value_bets_df.columns
    assert "expected_value" in value_bets_df.columns
    assert value_bets_df["predicted_prob"].isnull().all()


def test_patch_winner_column():
    """
    Tests that the winner column is correctly patched to be integer 0 or 1.
    """
    data = {"winner": [1.0, 0.0, np.nan, 1, 0]}
    df = pd.DataFrame(data)

    patched_df = patch_winner_column(df)

    assert patched_df["winner"].dtype == int
    assert patched_df["winner"].tolist() == [1, 0, 0, 1, 0]
