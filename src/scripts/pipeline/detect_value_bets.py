import pandas as pd
from pathlib import Path

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import log_info, log_warning
from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
)
from scripts.utils.value_metrics import compute_value_metrics


def detect_value_bets(
    df: pd.DataFrame,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    max_margin: float = DEFAULT_MAX_MARGIN,
) -> pd.DataFrame:
    df = normalize_columns(df)
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
    df = pd.read_csv(input_csv)
    log_info(f"Loaded {len(df)} rows from {input_csv}")
    df_out = detect_value_bets(
        df,
        ev_threshold=ev_threshold,
        confidence_threshold=confidence_threshold,
        max_odds=max_odds,
        max_margin=max_margin,
    )
    out_path = Path(output_csv)
    if df_out.empty:
        log_warning("No value bets found after filtering.")
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Value bets written to {out_path}")
