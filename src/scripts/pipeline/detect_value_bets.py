import pandas as pd
from pathlib import Path

# ---- Canonical Imports ----
from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import setup_logging, log_info, log_warning
from scripts.utils.schema import enforce_schema
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
)
from scripts.utils.value_metrics import compute_value_metrics


# ---- Pure Function Core ----
def detect_value_bets(
    df: pd.DataFrame,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    max_margin: float = DEFAULT_MAX_MARGIN,
) -> pd.DataFrame:
    """
    Identify value bets based on expected value, confidence, odds, and margin thresholds.
    Pure function: DataFrame in, DataFrame out.
    """
    # Add derived metrics if missing
    if "expected_value" not in df.columns or "kelly_fraction" not in df.columns:
        df = compute_value_metrics(df)
    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]

    mask = (
        (df["expected_value"] >= ev_threshold)
        & (df["confidence_score"] >= confidence_threshold)
        & (df["odds"] <= max_odds)
    )
    if "odds_margin" in df.columns:
        mask &= df["odds_margin"] <= max_margin

    df_filtered = df[mask].copy()
    return enforce_schema(df_filtered, "value_bets")


# ---- CLI Entrypoint ----
@cli_entrypoint
def main(
    input_csv: str,
    output_csv: str,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    max_margin: float = DEFAULT_MAX_MARGIN,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint for value bet detection.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    in_path = Path(input_csv)
    out_path = Path(output_csv)

    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    df = pd.read_csv(in_path)
    log_info(f"Loaded {len(df)} rows from {in_path}")

    df_out = detect_value_bets(
        df,
        ev_threshold=ev_threshold,
        confidence_threshold=confidence_threshold,
        max_odds=max_odds,
        max_margin=max_margin,
    )

    if df_out.empty:
        log_warning("No value bets found after filtering.")

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Value bets written to {out_path}")
