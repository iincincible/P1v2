"""
Utilities for data validation.
"""

import pandas as pd


class ValidationError(Exception):
    """Custom exception for data validation errors."""

    pass


def validate_value_bets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates a DataFrame containing value bet data.

    Checks for:
    - Odds are greater than 1.
    - Predicted probabilities are between 0 and 1.
    - Key columns do not contain null values.

    :param df: The DataFrame to validate.
    :return: The original DataFrame if validation passes.
    :raises: ValidationError if any checks fail.
    """
    if "odds" in df.columns:
        if not (df["odds"] > 1).all():
            raise ValidationError(
                "Validation failed: Found odds less than or equal to 1."
            )

    if "predicted_prob" in df.columns:
        if not df["predicted_prob"].between(0, 1).all():
            raise ValidationError(
                "Validation failed: Found predicted probabilities outside the [0, 1] range."
            )

    required_cols = ["match_id", "player_1", "player_2", "odds", "predicted_prob"]
    missing_vals = df[required_cols].isnull().sum()
    if missing_vals.sum() > 0:
        raise ValidationError(
            f"Validation failed: Found missing values in key columns:\n{missing_vals[missing_vals > 0]}"
        )

    return df
