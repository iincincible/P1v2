import argparse
import joblib
import pandas as pd
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_error, log_dryrun
from scripts.utils.cli_utils import (
    add_common_flags,
    should_run,
    assert_file_exists,
    assert_columns_exist,
)
from scripts.utils.normalize_columns import normalize_columns


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

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would load model {_args.model_file}, predict on {_args.input_csv} → {_args.output_csv}"
        )
        return

    model_path = Path(_args.model_file)
    input_path = Path(_args.input_csv)
    output_path = Path(_args.output_csv)

    assert_file_exists(model_path, "model_file")
    assert_file_exists(input_path, "input_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        model = joblib.load(model_path)
        log_info(f"📥 Loaded model from {model_path}")
    except Exception as e:
        log_error(f"❌ Failed to load model: {e}")
        return

    try:
        df = pd.read_csv(input_path)
        log_info(f"📥 Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        log_error(f"❌ Failed to read input CSV: {e}")
        return

    df = normalize_columns(df)
    try:
        assert_columns_exist(df, _args.features, context="prediction")
    except Exception as e:
        log_error(f"❌ Missing features: {e}")
        return

    try:
        df["predicted_prob"] = model.predict_proba(df[_args.features])[:, 1]
    except Exception as e:
        log_error(f"❌ Prediction failed: {e}")
        return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"✅ Saved predictions to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save predictions: {e}")


if __name__ == "__main__":
    main()
