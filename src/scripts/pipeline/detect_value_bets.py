import argparse
import pandas as pd
import numpy as np
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_warning,
    log_success,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import (
    add_common_flags,
    should_run,
    assert_file_exists,
    assert_columns_exist,
)
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.constants import DEFAULT_MAX_MARGIN


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Filter predictions to find +EV value bets."
    )
    parser.add_argument("--input_csv", required=True, help="Predictions input CSV")
    parser.add_argument(
        "--output_csv", required=True, help="Path to save filtered value bets"
    )
    parser.add_argument(
        "--ev_threshold", type=float, default=0.2, help="Minimum expected value"
    )
    parser.add_argument(
        "--confidence_threshold",
        type=float,
        default=0.4,
        help="Minimum confidence score",
    )
    parser.add_argument(
        "--max_odds", type=float, default=6.0, help="Maximum allowed odds"
    )
    parser.add_argument(
        "--max_margin",
        type=float,
        default=DEFAULT_MAX_MARGIN,
        help="Maximum odds margin",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run: log and exit
    if _args.dry_run:
        log_dryrun(
            f"Would load predictions from {_args.input_csv}, "
            f"filter EV>={_args.ev_threshold}, "
            f"conf>={_args.confidence_threshold}, "
            f"odds<={_args.max_odds}, "
            f"margin<={_args.max_margin}, "
            f"then write to {_args.output_csv}"
        )
        return

    input_path = Path(_args.input_csv)
    assert_file_exists(input_path, "input_csv")

    output_path = Path(_args.output_csv)
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    # Load
    try:
        df = pd.read_csv(input_path)
        log_info(f"📥 Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        log_error(f"❌ Failed to read {input_path}: {e}")
        return

    # Normalize & compute EV
    try:
        df = normalize_columns(df)
        df = add_ev_and_kelly(df)
        df = patch_winner_column(df)
    except Exception as e:
        log_error(f"❌ Failed to normalize/add EV: {e}")
        return

    # Ensure confidence_score exists
    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]
        log_info("🔧 Set confidence_score = predicted_prob")

    # Validate required columns
    required = ["expected_value", "odds", "predicted_prob", "confidence_score"]
    try:
        assert_columns_exist(df, required, context="value bet filter")
    except Exception as e:
        log_error(f"❌ Missing required columns: {e}")
        return

    # Drop inf / NaN
    before = len(df)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    dropped = before - len(df)
    if dropped > 0:
        log_warning(f"⚠️ Dropped {dropped} rows with NaN or inf in required columns")

    # Filter
    filt = (
        (df["expected_value"] >= _args.ev_threshold)
        & (df["confidence_score"] >= _args.confidence_threshold)
        & (df["odds"] <= _args.max_odds)
    )
    if "odds_margin" in df.columns:
        filt &= df["odds_margin"] <= _args.max_margin

    df_filtered = df[filt]
    if df_filtered.empty:
        log_warning("⚠️ No value bets found after filtering.")
        return

    # Save
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(output_path, index=False)
        log_success(f"✅ Saved {len(df_filtered)} value bets to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save filtered bets: {e}")


if __name__ == "__main__":
    main()
