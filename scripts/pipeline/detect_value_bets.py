import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.ev import compute_ev
from scripts.utils.logger import log_info, log_warning, log_success
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.filters import filter_value_bets
from scripts.utils.constants import DEFAULT_MAX_MARGIN


def main():
    parser = argparse.ArgumentParser(description="Filter predictions to find +EV value bets.")
    parser.add_argument("--input_csv", required=True, help="Path to predictions CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save filtered value bets")
    parser.add_argument("--ev_threshold", type=float, default=0.2)
    parser.add_argument("--confidence_threshold", type=float, default=0.4)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN)
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.input_csv, "predictions file")

    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)

    if "expected_value" not in df.columns:
        df["expected_value"] = compute_ev(
            df["predicted_prob"], df["odds"], df.get("implied_prob", None)
        )
        log_info("🔧 Computed expected_value from predicted_prob and odds")

    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]
        log_info("🔧 Set confidence_score = predicted_prob")

    required = ["expected_value", "odds", "predicted_prob", "confidence_score"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"❌ Required column missing: {col}")

    df_filtered = df[
        (df["expected_value"] >= args.ev_threshold) &
        (df["confidence_score"] >= args.confidence_threshold) &
        (df["odds"] <= args.max_odds)
    ]
    if "odds_margin" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["odds_margin"] <= args.max_margin]

    if df_filtered.empty:
        log_warning("⚠️ No value bets after filtering.")
        return

    df_filtered = patch_winner_column(df_filtered)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(output_path, index=False)
    log_success(f"✅ Saved {len(df_filtered)} value bets to {output_path}")


if __name__ == "__main__":
    main()
