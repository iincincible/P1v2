# src/scripts/pipeline/build_odds_features.py

import numpy as np
import pandas as pd

from scripts.utils.logger import log_info
from scripts.utils.schema import enforce_schema, normalize_columns


def build_odds_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds implied probability and bookmaker margin features to a DataFrame.

    :param df: The input DataFrame, expected to contain 'ltp_player_1' and 'ltp_player_2' columns.
    :return: A new DataFrame with added feature columns.
    """
    df = normalize_columns(df)
    df = df.copy()
    if "ltp_player_1" in df.columns and "ltp_player_2" in df.columns:
        df["ltp_player_1"] = pd.to_numeric(df["ltp_player_1"], errors="coerce")
        df["ltp_player_2"] = pd.to_numeric(df["ltp_player_2"], errors="coerce")
        df["implied_prob_1"] = 1 / df["ltp_player_1"].replace(0, np.nan)
        df["implied_prob_2"] = 1 / df["ltp_player_2"].replace(0, np.nan)
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
        log_info("Added implied probability and margin features.")
    else:
        for col in [
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ]:
            df[col] = np.nan
        log_info("Missing LTP columns; filled features with NaN.")
    return enforce_schema(df, schema_name="features")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Build odds features")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.input_csv)
    result = build_odds_features(df)
    if not args.dry_run:
        result.to_csv(args.output_csv, index=False)
        log_info(f"Features written to {args.output_csv}")


if __name__ == "__main__":
    main_cli()
