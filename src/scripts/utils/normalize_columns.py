# File: src/scripts/utils/normalize_columns.py

import pandas as pd
import logging

CANONICAL_RENAME_MAP = {
    "prob": "predicted_prob",
    "model_prob": "predicted_prob",
    "ev": "expected_value",
    "value": "expected_value",
    "odds_player_1": "odds",
    "odds1": "odds",
    "odds2": "odds",
    "Player1": "player_1",
    "Player2": "player_2",
    "runner_1": "player_1",
    "runner_2": "player_2",
    "actualWinner": "actual_winner",
    "winner_name": "actual_winner",
}

CANONICAL_REQUIRED_COLUMNS = [
    "player_1",
    "player_2",
    "odds",
    "predicted_prob",
    "expected_value",
    "winner",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names if possible."""
    return df.rename(
        columns={k: v for k, v in CANONICAL_RENAME_MAP.items() if k in df.columns}
    )


def patch_winner_column(df: pd.DataFrame) -> pd.DataFrame:
    """Patch or create 'winner' column in canonical 0/1 format, fallback to NaN if not possible."""
    # Already OK
    if "winner" in df.columns and set(df["winner"].dropna().unique()).issubset({0, 1}):
        return df

    # Derive from actual_winner vs player_1
    if "actual_winner" in df.columns and "player_1" in df.columns:
        df["winner"] = (df["actual_winner"] == df["player_1"]).astype(int)
        return df

    # No info, fill with NaN and warn
    logging.warning("No legitimate winner label available; filling 'winner' with NaN.")
    df["winner"] = float("nan")
    return df


def enforce_canonical_columns(
    df: pd.DataFrame, required=CANONICAL_REQUIRED_COLUMNS, context=""
):
    """Raise if any required canonical columns are missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"❌ Missing required columns after output in {context}: {missing}"
        )
    return True


def assert_required_columns(
    df: pd.DataFrame, required=CANONICAL_REQUIRED_COLUMNS, context=""
):
    """Raise if required columns are missing, with clear error."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Required columns missing in {context}: {missing}")
    return True


def normalize_and_patch_canonical_columns(df: pd.DataFrame, context="") -> pd.DataFrame:
    """Full robust patch pipeline. Normalizes, patches, and fills all canonical columns as needed."""
    # 1. Rename to canonical names
    df = normalize_columns(df)

    # 2. Patch/generate 'winner' column if possible
    try:
        df = patch_winner_column(df)
    except Exception as e:
        logging.warning(f"patch_winner_column failed: {e}; filling with NaN.")
        df["winner"] = float("nan")

    # 3. All canonical columns: fill missing as NaN and warn
    for col in CANONICAL_REQUIRED_COLUMNS:
        if col not in df.columns:
            logging.warning(
                f"[PATCH] Adding missing canonical column: {col} (filled with NaN) for context {context}"
            )
            df[col] = float("nan")

    # 4. Optionally: enforce types, reorder columns
    ordered_cols = [c for c in CANONICAL_REQUIRED_COLUMNS if c in df.columns]
    all_cols = ordered_cols + [c for c in df.columns if c not in ordered_cols]
    return df[all_cols]


def prepare_value_bets_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Example utility: runs normalization, adds EV/Kelly if missing,
    patches winner column for value bets analysis.
    """
    from scripts.utils.betting_math import add_ev_and_kelly

    df = normalize_and_patch_canonical_columns(df, context="prepare_value_bets_df")
    # Add EV and Kelly if not present
    if "expected_value" not in df.columns or "kelly_stake" not in df.columns:
        try:
            df = add_ev_and_kelly(df)
        except Exception as e:
            logging.warning(f"Could not add EV/Kelly columns: {e}")
    try:
        df = patch_winner_column(df)
    except Exception as e:
        logging.warning(f"Could not patch winner column: {e}")
    return df


def patch_to_canonical_predictions_file(
    path, inplace=True, output_path=None, context="patch_to_canonical_predictions_file"
):
    """
    Reads a CSV, robustly renames and patches all canonical columns, and writes out a fully pipeline-compatible file.
    If inplace=True, overwrites the input file. Otherwise writes to output_path (required).
    """
    df = pd.read_csv(path)
    logging.info(f"Loaded {len(df)} rows from {path}")

    df = normalize_and_patch_canonical_columns(df, context=context)

    try:
        enforce_canonical_columns(df, context=context)
    except Exception as e:
        logging.warning(f"Patch output missing canonical columns after patch: {e}")

    if inplace:
        df.to_csv(path, index=False)
        logging.info(f"✅ Overwrote {path} with canonical columns: {list(df.columns)}")
    else:
        if output_path is None:
            raise ValueError("output_path must be specified if not inplace.")
        df.to_csv(output_path, index=False)
        logging.info(f"✅ Saved patched file to {output_path}")
    return df
