import pandas as pd
import pytest

from scripts.utils.config_utils import merge_with_defaults
from scripts.utils.normalize_columns import patch_winner_column


def test_pytest_works():
    """Sanity check: Pytest should find and run this test."""
    assert 1 + 1 == 2


def test_patch_winner_column():
    """patch_winner_column should map actual_winner → 1/0 for player_1 wins."""
    df = pd.DataFrame(
        {
            "player_1": ["Serena", "Venus", "Novak"],
            "player_2": ["Venus", "Serena", "Rafa"],
            "actual_winner": ["Serena", "Serena", "Rafa"],
        }
    )

    result = patch_winner_column(df)

    assert "winner" in result.columns
    # Serena wins (player_1), then Serena wins (not player_1), then Rafa wins
    assert list(result["winner"]) == [1, 0, 0]


@pytest.mark.parametrize(
    "defaults,config,expected",
    [
        ({"a": 1, "b": 2}, {"b": 22, "c": 3}, {"a": 1, "b": 22, "c": 3}),
        (
            {"a": 1, "b": {"x": 10, "y": 20}},
            {"b": {"y": 200}, "c": 3},
            {"a": 1, "b": {"x": 10, "y": 200}, "c": 3},
        ),
        ({"foo": 5}, {}, {"foo": 5}),
        ({"a": 1, "b": 2}, {"a": 9, "b": 8}, {"a": 9, "b": 8}),
    ],
)
def test_merge_with_defaults(defaults, config, expected):
    merged = merge_with_defaults(config, defaults)
    assert merged == expected

    # When config is empty, ensure default dict is not mutated
    if not config:
        assert merged is not defaults
