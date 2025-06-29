# src/scripts/pipeline/detect_value_bets.py

import pandas as pd
from scripts.utils.logger import log_info
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
)
from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.value_metrics import compute_value_metrics


def detect_value_bets(
    df: pd.DataFrame,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    max_margin: float = DEFAULT_MAX_MARGIN,
) -> pd.DataFrame:
    """
    Detect value bets with thresholds for EV, confidence, odds, and margin.
    """
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


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Detect value bets")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument(
        "--confidence_threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD
    )
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.input_csv)
    result = detect_value_bets(
        df,
        ev_threshold=args.ev_threshold,
        confidence_threshold=args.confidence_threshold,
        max_odds=args.max_odds,
        max_margin=args.max_margin,
    )
    if not args.dry_run:
        result.to_csv(args.output_csv, index=False)
        log_info(f"Value bets written to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
