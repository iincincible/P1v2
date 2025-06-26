"""
Filter predictions to find +EV value bets.
"""

import pandas as pd
from pathlib import Path

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager
from scripts.utils.constants import DEFAULT_MAX_MARGIN
from scripts.utils.value_metrics import compute_value_metrics

logger = getLogger(__name__)


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    ev_threshold: float = 0.2,
    confidence_threshold: float = 0.4,
    max_odds: float = 6.0,
    max_margin: float = DEFAULT_MAX_MARGIN,
    overwrite: bool = False,
    dry_run: bool = False,
):
    """
    Identify value bets based on expected value and confidence thresholds.
    """
    in_path = Path(input_csv)
    if not in_path.exists():
        logger.error("Input CSV not found: %s", in_path)
        raise FileNotFoundError(in_path)
    df = pd.read_csv(in_path)
    logger.info("Loaded %d rows from %s", len(df), in_path)

    # Ensure expected_value and kelly_fraction exist
    if "expected_value" not in df.columns or "kelly_fraction" not in df.columns:
        df = compute_value_metrics(df)

    # Ensure confidence_score column
    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]
        logger.debug("Set confidence_score = predicted_prob")

    before = len(df)
    mask = (
        (df["expected_value"] >= ev_threshold)
        & (df["confidence_score"] >= confidence_threshold)
        & (df["odds"] <= max_odds)
    )
    if "odds_margin" in df.columns:
        mask &= df["odds_margin"] <= max_margin

    df_filtered = df[mask]
    after = len(df_filtered)
    if df_filtered.empty:
        logger.warning("No value bets found after filtering.")
        df_out = pd.DataFrame(columns=SchemaManager._schemas["value_bets"]["order"])
        df_out = SchemaManager.patch_schema(df_out, "value_bets")
    else:
        df_out = SchemaManager.patch_schema(df_filtered, "value_bets")
        logger.info("Filtered %d of %d value bets.", after, before)

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out_path)
        return
    if dry_run:
        logger.info("Dry-run: would write %d rows to %s", len(df_out), out_path)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        logger.info("Value bets written to %s", out_path)
