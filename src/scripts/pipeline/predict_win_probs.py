"""
Predict win probabilities using a trained model.
"""

import pandas as pd
from pathlib import Path
import joblib

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)

DEFAULT_FEATURES = [
    "implied_prob_1",
    "implied_prob_2",
    "implied_prob_diff",
    "odds_margin",
]


@guarded_run
def main(
    model_file: str,
    input_csv: str,
    output_csv: str,
    overwrite: bool = False,
    dry_run: bool = False,
):
    """
    Load model and predict win probabilities for each match.
    """
    model_path = Path(model_file)
    if not model_path.exists():
        logger.error("Model file not found: %s", model_path)
        raise FileNotFoundError(model_path)
    try:
        model = joblib.load(model_path)
        logger.info("Loaded model from %s", model_path)
    except Exception as e:
        logger.error("Failed to load model: %s", e)
        return

    data_path = Path(input_csv)
    if not data_path.exists():
        logger.error("Input CSV not found: %s", data_path)
        raise FileNotFoundError(data_path)
    df = pd.read_csv(data_path)
    logger.info("Loaded %d rows from %s", len(df), data_path)

    features = getattr(model, "feature_names_in_", DEFAULT_FEATURES)
    missing = [f for f in features if f not in df.columns]
    if missing:
        logger.warning("Model expects missing features %s; filling with NaN", missing)
        for f in missing:
            df[f] = pd.NA

    initial_len = len(df)
    df_valid = df.dropna(subset=features)
    dropped = initial_len - len(df_valid)
    if dropped:
        logger.warning("Dropped %d rows with NaN features", dropped)
    if df_valid.empty:
        logger.error("No rows left after dropping NaNs; writing empty output.")
        empty_df = pd.DataFrame(columns=SchemaManager._schemas["predictions"]["order"])
        df_out = SchemaManager.patch_schema(empty_df, "predictions")
    else:
        try:
            if hasattr(model, "predict_proba"):
                df_valid["predicted_prob"] = model.predict_proba(df_valid[features])[
                    :, 1
                ]
            else:
                df_valid["predicted_prob"] = model.predict(df_valid[features])
            logger.info("Added predicted_prob column.")
        except Exception as e:
            logger.error("Prediction failed: %s", e)
            df_valid["predicted_prob"] = pd.NA
        df_out = SchemaManager.patch_schema(df_valid, "predictions")

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out_path)
        return
    if dry_run:
        logger.info("Dry-run: would write %d rows to %s", len(df_out), out_path)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        logger.info("Predictions written to %s", out_path)
