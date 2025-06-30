# tests/pipeline/test_detect_value_bets.py

import pandas as pd

from scripts.pipeline.detect_value_bets import detect_value_bets


def test_detect_value_bets_integration():
    """
    Tests the detect_value_bets function to ensure it correctly
    filters bets based on EV, confidence, and odds thresholds.
    """
    # Create sample input data
    data = {
        "match_id": ["m1", "m2", "m3", "m4"],
        "player_1": ["A", "B", "C", "D"],
        "player_2": ["X", "Y", "Z", "W"],
        "predicted_prob": [0.6, 0.5, 0.2, 0.8],  # Confidence score will be same
        "odds": [2.0, 1.9, 6.0, 1.5],
        "winner": [1, 0, 0, 1],
    }
    df = pd.DataFrame(data)

    # EV for each row:
    # m1: (0.6 * 1.0) - 0.4 = 0.2 (Value bet)
    # m2: (0.5 * 0.9) - 0.5 = -0.05 (Not value)
    # m3: (0.2 * 5.0) - 0.8 = 0.2 (Value bet)
    # m4: (0.8 * 0.5) - 0.2 = 0.2 (Value bet)

    # --- Test Case 1: Default EV threshold (0.05) ---
    result_df = detect_value_bets(
        df,
        ev_threshold=0.05,
        confidence_threshold=0.5,  # m1, m4 pass
        max_odds=7.0,  # all pass
    )
    # Only m1 and m4 should pass both EV and confidence thresholds
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 2
    assert set(result_df["match_id"]) == {"m1", "m4"}

    # --- Test Case 2: Higher EV threshold ---
    result_df_high_ev = detect_value_bets(df, ev_threshold=0.21)  # No bets should pass
    assert len(result_df_high_ev) == 0

    # --- Test Case 3: Stricter max_odds ---
    result_df_max_odds = detect_value_bets(df, max_odds=5.0)  # m3 should fail
    assert len(result_df_max_odds) == 2
    assert "m3" not in result_df_max_odds["match_id"].tolist()
