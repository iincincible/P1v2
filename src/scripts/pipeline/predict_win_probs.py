import argparse
import joblib
import pandas as pd
import logging

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,  # <-- Make sure this is included!
    )
from scripts.utils.cli_utils import (
    add_common_flags,
    assert_file_exists,
    assert_columns_exist,
    output_file_guard,
)
from scripts.utils.normalize_columns import normalize_columns, enforce_canonical_columns

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)


@output_file_guard(output_arg="output_csv")
def predict_win_probs(
    model_file,
    input_csv,
    output_csv,
    features,
    overwrite=False,
    dry_run=False,
):
    assert_file_exists(model_file, "model_file")
    assert_file_exists(input_csv, "input_csv")

    model = joblib.load(model_file)
    log_info(f"📥 Loaded model from {model_file}")

    df = pd.read_csv(input_csv)
    log_info(f"📥 Loaded {len(df)} rows from {input_csv}")
    df = normalize_columns(df)
    assert_columns_exist(df, features, context="prediction")

    df["predicted_prob"] = model.predict_proba(df[features])[:, 1]

    # Refactor: Enforce canonical columns at output, if possible
    try:
        enforce_canonical_columns(df, context="predict win probs")
    except Exception as e:
        log_warning(f"Canonical column check failed: {e}")

    df.to_csv(output_csv, index=False)
    log_success(f"✅ Saved predictions to {output_csv}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Use trained model to predict win probabilities."
    )
    parser.add_argument(
        "--model_file", required=True, help="Trained sklearn model (joblib)"
    )
    parser.add_argument(
        "--input_csv", required=True, help="Input CSV with feature columns"
    )
    parser.add_argument("--output_csv", required=True, help="Path to save predictions")
    parser.add_argument(
        "--features",
        nargs="+",
        default=[
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ],
        help="Feature columns for prediction",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    predict_win_probs(
        model_file=_args.model_file,
        input_csv=_args.input_csv,
        output_csv=_args.output_csv,
        features=_args.features,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )


if __name__ == "__main__":
    main()
