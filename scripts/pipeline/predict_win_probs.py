import argparse
import joblib
import pandas as pd
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists, assert_columns_exist
from scripts.utils.normalize_columns import normalize_columns


def main():
    parser = argparse.ArgumentParser(description="Use trained model to predict win probabilities.")
    parser.add_argument("--model_file", required=True, help="Trained sklearn model (joblib)")
    parser.add_argument("--input_csv", required=True, help="Input CSV with feature columns")
    parser.add_argument("--output_csv", required=True, help="Path to save predictions")
    parser.add_argument("--features", nargs="+", default=[
        "implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"
    ])
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.input_csv, "input_csv")
    assert_file_exists(args.model_file, "model_file")

    model = joblib.load(args.model_file)
    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)

    assert_columns_exist(df, args.features, context="prediction")

    df["predicted_prob"] = model.predict_proba(df[args.features])[:, 1]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_success(f"✅ Saved predictions to {output_path}")


if __name__ == "__main__":
    main()
