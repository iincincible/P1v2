import pandas as pd
import numpy as np
from pathlib import Path
from scripts.utils.logger import log_info, log_warning
from scripts.utils.schema import normalize_columns, enforce_schema


def run_build_odds_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Adds implied probabilities and margin features to a matches DataFrame.
    Returns result with enforced schema.
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
        log_warning("Missing LTP columns; filled features with NaN.")
    return enforce_schema(df, schema_name="features")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build odds features for match DataFrame"
    )
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.input_csv)
    log_info(f"Loaded {len(df)} rows from {args.input_csv}")
    df_out = run_build_odds_features(df)
    out_path = Path(args.output_csv)
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Features written to {out_path}")


if __name__ == "__main__":
    main_cli()
