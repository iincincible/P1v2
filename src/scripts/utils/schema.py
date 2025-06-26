import pandas as pd
from scripts.utils.logger import getLogger

logger = getLogger(__name__)


class SchemaManager:
    """
    Central registry for CSV schemas.
    Defines required/optional columns and enforces or patches DataFrames.
    """

    # Example schemas; extend as needed
    _schemas = {
        "matches": {
            "required": [
                "match_id",
                "market",
                "selection",
                "ltp",
                "volume",
                "timestamp",
            ],
            # If you care about column order, list them here; otherwise keys order is fine.
            "order": ["match_id", "market", "selection", "ltp", "volume", "timestamp"],
        },
        # Add other schemas: "predictions", "value_bets", etc.
    }

    @classmethod
    def assert_schema(cls, df: pd.DataFrame, schema_name: str):
        """Raise if the DataFrame is missing any required columns."""
        schema = cls._schemas.get(schema_name)
        if not schema:
            raise ValueError(f"Unknown schema '{schema_name}'")
        missing = set(schema["required"]) - set(df.columns)
        if missing:
            raise ValueError(
                f"DataFrame for schema '{schema_name}' is missing columns: {missing}"
            )

    @classmethod
    def patch_schema(cls, df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
        """
        Ensure the DataFrame has the required columns,
        adding them as NaN if missing, and reordering.
        """
        schema = cls._schemas.get(schema_name)
        if not schema:
            raise ValueError(f"Unknown schema '{schema_name}'")

        # Add any missing required columns
        for col in schema["required"]:
            if col not in df.columns:
                logger.debug(
                    "Adding missing column '%s' to '%s' schema", col, schema_name
                )
                df[col] = pd.NA

        # Reorder (extra columns will be appended at the end)
        ordered = schema.get("order", schema["required"])
        existing = [c for c in ordered if c in df.columns]
        extras = [c for c in df.columns if c not in existing]
        return df[existing + extras]
