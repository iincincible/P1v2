"""
Generate implied probability and margin features from odds data.
"""

import pandas as pd
import numpy as np
from pathlib import Path

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    overwrite: bool = False,
    dry_run: bool = False,
):
    """
    Build odds-derived features for each match.

    Args:
        input_csv: Path to CSV containing 'ltp_player_1' and 'ltp_player_2' columns.
        output_csv: Path to write the features CSV.
        overwrite: If True, overwrite existing output file.
        dry_run: If True, simulate without writing any files.
    """
    in_path = Path(input_csv)
    if not in_path.exists():
        logger.error("Input CSV not found: %s", in_path)
        raise FileNotFoundError(in_path)

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out_path)
        return

    df = pd.read_csv(in_path)
    logger.info("Loaded %d rows from %s", len(df), in_path)

    # Feature engineering: implied probabilities and margin
    if "ltp_player_1" in df.columns and "ltp_player_2" in df.columns:
        # Convert odds to numeric and compute
        df["ltp_player_1"] = pd.to_numeric(df["ltp_player_1"], errors="coerce")
        df["ltp_player_2"] = pd.to_numeric(df["ltp_player_2"], errors="coerce")
        df["implied_prob_1"] = 1 / df["ltp_player_1"].replace(0, np.nan)
        df["implied_prob_2"] = 1 / df["ltp_player_2"].replace(0, np.nan)
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
        logger.info("Added implied probability and margin features.")
    else:
        for col in [
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ]:
            df[col] = np.nan
        logger.warning(
            "Missing 'ltp_player_1' or 'ltp_player_2'; filled feature columns with NaN."
        )

    # Warn if any NaNs in implied probabilities
    if df[["implied_prob_1", "implied_prob_2"]].isnull().any().any():
        logger.warning(
            "Some implied probabilities are NaN (possibly due to missing or zero LTPs)."
        )

    # Enforce schema for features
    df_out = SchemaManager.patch_schema(df, schema_name="features")

    # Write or simulate output
    if dry_run:
        logger.info("Dry-run: would write %d rows to %s", len(df_out), out_path)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        logger.info("Features written to %s", out_path)


if __name__ == "__main__":
    main()
