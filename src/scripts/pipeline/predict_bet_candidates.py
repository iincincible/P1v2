import argparse
import logging

import pandas as pd
import joblib

from scripts.utils.logging_config import setup_logging
from scripts.utils.cli_utils import guarded_run
from scripts.utils.columns import validate_columns


@guarded_run(output_arg="output")
def run():
    parser = argparse.ArgumentParser(
        description="Generate predictions for bet candidates."
    )

    # dry-run & overwrite flags
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate but do not write any output.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output file if present.",
    )

    # logging flags
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG-level logging to console."
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Write a copy of all logs here."
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Emit structured JSON logs (needs python-json-logger).",
    )

    # core inputs & outputs
    parser.add_argument(
        "--input", required=True, help="Path to the input CSV for prediction."
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Path to the trained predictor model pickle file.",
    )
    parser.add_argument(
        "--output", required=True, help="Path to write the predictions CSV."
    )

    args = parser.parse_args()

    # initialize centralized logging
    setup_logging(
        level="DEBUG" if args.verbose else "INFO",
        log_file=args.log_file,
        json_logs=args.json_logs,
    )
    logger = logging.getLogger(__name__)

    # load input data
    logger.info("Loading input data from %s", args.input)
    df_in = pd.read_csv(args.input)
    logger.debug("Input data preview:\n%s", df_in.head())

    # load model
    logger.info("Loading model from %s", args.model)
    model = joblib.load(args.model)

    # make predictions
    logger.info("Making predictions…")
    df_in["prediction"] = model.predict(df_in)
    logger.debug("Predictions preview:\n%s", df_in.head())

    # enforce canonical schema
    validate_columns(df_in, "predictions")

    return args, df_in


if __name__ == "__main__":
    run()
