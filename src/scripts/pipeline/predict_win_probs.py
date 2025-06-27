import pandas as pd
from pathlib import Path
import joblib

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import setup_logging, log_info, log_warning
from scripts.utils.schema import enforce_schema

DEFAULT_FEATURES = [
    "implied_prob_1",
    "implied_prob_2",
    "implied_prob_diff",
    "odds_margin",
]


def predict_win_probs(
    model,
    df: pd.DataFrame,
    features=None,
) -> pd.DataFrame:
    """
    Use a trained model to predict win probabilities for each match.
    Returns DataFrame with enforced schema.
    """
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


@cli_entrypoint
def main(
    model_file: str,
    input_csv: str,
    output_csv: str,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Predict win probabilities for each match using a model.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    model_path = Path(model_file)
    data_path = Path(input_csv)
    out_path = Path(output_csv)

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {data_path}")
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    model = joblib.load(model_path)
    log_info(f"Loaded model from {model_path}")

    df = pd.read_csv(data_path)
    log_info(f"Loaded {len(df)} rows from {data_path}")

    df_out = predict_win_probs(model, df)

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Predictions written to {out_path}")
