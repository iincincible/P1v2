import pandas as pd
from pathlib import Path
import joblib
from scripts.utils.logger import log_info, log_warning
from scripts.utils.schema import normalize_columns, enforce_schema

DEFAULT_FEATURES = [
    "implied_prob_1",
    "implied_prob_2",
    "implied_prob_diff",
    "odds_margin",
]


def run_predict_win_probs(model, df: pd.DataFrame, features=None) -> pd.DataFrame:
    """
    Adds win probability predictions to the input DataFrame.
    """
    df = normalize_columns(df)
    if features is None:
        features = getattr(model, "feature_names_in_", DEFAULT_FEATURES)
    missing = [f for f in features if f not in df.columns]
    for f in missing:
        df[f] = pd.NA
        log_warning(f"Model expects missing feature: {f} (filled with NaN)")
    df_valid = df.dropna(subset=features)
    if df_valid.empty:
        log_warning("No rows left after dropping NaNs; writing empty output.")
        empty_df = pd.DataFrame(
            columns=enforce_schema(pd.DataFrame(), "predictions").columns
        )
        return enforce_schema(empty_df, "predictions")
    try:
        if hasattr(model, "predict_proba"):
            df_valid["predicted_prob"] = model.predict_proba(df_valid[features])[:, 1]
        else:
            df_valid["predicted_prob"] = model.predict(df_valid[features])
        log_info("Added predicted_prob column.")
    except Exception as e:
        log_warning(f"Prediction failed: {e}")
        df_valid["predicted_prob"] = pd.NA
    return enforce_schema(df_valid, "predictions")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Predict win probabilities")
    parser.add_argument("--model_file", required=True)
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    model = joblib.load(args.model_file)
    log_info(f"Loaded model from {args.model_file}")
    df = pd.read_csv(args.input_csv)
    log_info(f"Loaded {len(df)} rows from {args.input_csv}")
    df_out = run_predict_win_probs(model, df)
    out_path = Path(args.output_csv)
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Predictions written to {out_path}")


if __name__ == "__main__":
    main_cli()
