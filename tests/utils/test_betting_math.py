# tests/utils/test_betting_math.py

import numpy as np
import pandas as pd

from scripts.utils.betting_math import add_ev_and_kelly


def test_add_ev_and_kelly():
    """
    Tests the calculation of Expected Value (EV) and Kelly Fraction.
    """
    # Create a sample DataFrame
    data = {"predicted_prob": [0.5, 0.2, 0.8], "odds": [2.5, 5.0, 1.2]}
    df = pd.DataFrame(data)

    # Apply the function
    result_df = add_ev_and_kelly(df)

    # --- Assertions ---
    # Expected EV = (prob * (odds - 1)) - (1 - prob)
    # Row 1: (0.5 * 1.5) - 0.5 = 0.75 - 0.5 = 0.25
    # Row 2: (0.2 * 4.0) - 0.8 = 0.8 - 0.8 = 0.0
    # Row 3: (0.8 * 0.2) - 0.2 = 0.16 - 0.2 = -0.04
    expected_ev = [0.25, 0.0, -0.04]

    # Expected Kelly = EV / (odds - 1)
    # Row 1: 0.25 / 1.5 = 0.1666...
    # Row 2: 0.0 / 4.0 = 0.0
    # Row 3: -0.04 / 0.2 = -0.2
    expected_kelly = [0.166667, 0.0, -0.2]

    assert "expected_value" in result_df.columns
    assert "kelly_fraction" in result_df.columns
    assert np.allclose(result_df["expected_value"], expected_ev)
    assert np.allclose(result_df["kelly_fraction"], expected_kelly)
