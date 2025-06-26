from typing import List, Dict
import pandas as pd
from .errors import ValidationError

# Define your “canonical” schemas here
CANONICAL_COLUMNS: Dict[str, List[str]] = {
    "matches": [
        "match_id",
        "tour",
        "tournament",
        "year",
        "player1_id",
        "player2_id",
        "winner_id",
        # …add any other required fields
    ],
    "bet_candidates": [
        "candidate_id",
        "score",
        # …fill in as appropriate
    ],
    "predictions": [
        "prediction",
        # …etc.
    ],
}


def validate_columns(df: pd.DataFrame, schema: str) -> None:
    """
    Ensure df contains all required columns for the given schema.
    Raises ValidationError if any are missing.
    """
    required = CANONICAL_COLUMNS.get(schema)
    if required is None:
        raise KeyError(f"No canonical‐column schema named '{schema}'")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValidationError(f"Missing required columns for '{schema}': {missing}")
