import argparse
import pandas as pd
import joblib
from sklearn.impute import SimpleImputer
from scripts.utils.normalize_columns import normalize_columns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    print(f"📥 Loading input: {args.input_csv}")
    df = pd.read_csv(args.input_csv)
    print(f"📆 Input shape: {df.shape}")

    print(f"📦 Loading model: {args.model_path}")
    model = joblib.load(args.model_path)

    df, feature_df = normalize_columns(df, return_features=True)

    expected_features = list(model.feature_names_in_)
    available_columns = list(feature_df.columns)
    print("🔎 Expected features:", expected_features)
    print("📋 Available columns:", available_columns)

    # Check for missing features
    matched_features = [f for f in expected_features if f in feature_df.columns]
    if not matched_features:
        raise ValueError(
            f"❌ No matching features found between model and input CSV.\n"
            f"Model expects: {expected_features}\n"
            f"But input has: {available_columns}"
        )

    # Subset and impute
    X = feature_df[matched_features]
    imputer = SimpleImputer(strategy="mean")
    X_imputed = imputer.fit_transform(X)

    preds = model.predict_proba(X_imputed)[:, 1]
    df["predicted_prob"] = preds

    print(f"💾 Saving predictions to {args.output_csv}")
    df.to_csv(args.output_csv, index=False)


if __name__ == "__main__":
    main()
