import argparse
import pandas as pd
import joblib
from pathlib import Path
from sklearn.impute import SimpleImputer

from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.cli_utils import add_common_flags, should_run
from scripts.utils.logger import log_info, log_success, log_warning


def main():
    parser = argparse.ArgumentParser(description="Predict win probabilities using a trained model.")
    parser.add_argument("--input_csv", required=True, help="Input CSV with features")
    parser.add_argument("--model_path", required=True, help="Path to trained model")
    parser.add_argument("--output_csv", required=True, help="Path to save predictions")
    add_common_flags(parser)
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    input_path = Path(args.input_csv)
    model_path = Path(args.model_path)
    output_path = Path(args.output_csv)

    log_info(f"📥 Loading input: {input_path}")
    df = pd.read_csv(input_path)
    log_info(f"📆 Input shape: {df.shape}")

    log_info(f"📦 Loading model: {model_path}")
    model = joblib.load(model_path)

    df, feature_df = normalize_columns(df, return_features=True)

    expected_features = list(model.feature_names_in_)
    available_columns = list(feature_df.columns)
    log_info(f"🔎 Expected features: {expected_features}")
    log_info(f"📋 Available columns: {available_columns}")

    matched_features = [f for f in expected_features if f in feature_df.columns]
    if not matched_features:
        raise ValueError(
            f"❌ No matching features found between model and input CSV.\n"
            f"Model expects: {expected_features}\n"
            f"But input has: {available_columns}"
        )

    X = feature_df[matched_features]
    imputer = SimpleImputer(strategy="mean")
    X_imputed = imputer.fit_transform(X)

    preds = model.predict_proba(X_imputed)[:, 1]
    df["predicted_prob"] = preds

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_success(f"✅ Saved predictions to {output_path}")


if __name__ == "__main__":
    main()
