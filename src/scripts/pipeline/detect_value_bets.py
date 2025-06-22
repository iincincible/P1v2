"""
Pipeline Stage: detect_value_bets.py

Inputs:
  - CSV with at least columns: player_1, player_2, odds, predicted_prob, expected_value, winner

Outputs:
  - CSV with filtered value bets, containing columns:
      player_1, player_2, odds, predicted_prob, expected_value, winner, confidence_score, kelly_stake
"""

import argparse
import pandas as pd
from pathlib import Path
from scripts.utils.logger import log_info, log_success, log_warning, log_error, log_dryrun
from scripts.utils.cli_utils import add_common_flags, dry_run_guard
from scripts.utils.normalize_columns import prepare_value_bets_df, assert_required_columns, CANONICAL_REQUIRED_COLUMNS
from scripts.utils.constants import DEFAULT_MAX_MARGIN

@dry_run_guard(file_args=["output_csv"])
def detect_value_bets(
    input_csv,
    output_csv,
    ev_threshold=0.2,
    confidence_threshold=0.4,
    max_odds=6.0,
    max_margin=DEFAULT_MAX_MARGIN,
    overwrite=False,
    dry_run=False,
):
    """
    Filters and outputs only value bets (+EV) from a predictions CSV.

    Output columns:
      - player_1, player_2, odds, predicted_prob, expected_value, winner, confidence_score, kelly_stake
    """
    try:
        df = pd.read_csv(input_csv)
        log_info(f"📥 Loaded {len(df)} rows from {input_csv}")
    except Exception as e:
        log_error(f"❌ Failed to read {input_csv}: {e}")
        return

    df = prepare_value_bets_df(df)
    assert_required_columns(df, CANONICAL_REQUIRED_COLUMNS, context="value bet pipeline")

    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]
        log_info("🔧 Set confidence_score = predicted_prob")

    before = len(df)
    filt = (
        (df["expected_value"] >= ev_threshold)
        & (df["confidence_score"] >= confidence_threshold)
        & (df["odds"] <= max_odds)
    )
    if "odds_margin" in df.columns:
        filt &= df["odds_margin"] <= max_margin

    df_filtered = df[filt]
    after = len(df_filtered)
    if df_filtered.empty:
        log_warning("⚠️ No value bets found after filtering.")
        return

    try:
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(output_csv, index=False)
        log_success(f"✅ Saved {after} value bets to {output_csv} (filtered from {before})")
    except Exception as e:
        log_error(f"❌ Failed to save filtered bets: {e}")

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Filter predictions to find +EV value bets."
    )
    parser.add_argument("--input_csv", required=True, help="Predictions input CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save filtered value bets")
    parser.add_argument("--ev_threshold", type=float, default=0.2, help="Minimum expected value")
    parser.add_argument("--confidence_threshold", type=float, default=0.4, help="Minimum confidence score")
    parser.add_argument("--max_odds", type=float, default=6.0, help="Maximum allowed odds")
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN, help="Maximum odds margin")
    add_common_flags(parser)
    _args = parser.parse_args(args)
    detect_value_bets(
        input_csv=_args.input_csv,
        output_csv=_args.output_csv,
        ev_threshold=_args.ev_threshold,
        confidence_threshold=_args.confidence_threshold,
        max_odds=_args.max_odds,
        max_margin=_args.max_margin,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
