import argparse
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def build_odds_features(input_csv, output_csv, overwrite=False, dry_run=False):
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logging.info(f"[SKIP] {output_csv} exists and --overwrite not set")
        return

    df = pd.read_csv(input_csv)
    logging.info(f"Loaded {len(df)} rows from {input_csv}")

    # Always create implied probability columns, filling with NaN where needed
    if "ltp_player_1" in df.columns and "ltp_player_2" in df.columns:
        # Convert to numeric (float), coerce errors to NaN
        df["ltp_player_1"] = pd.to_numeric(df["ltp_player_1"], errors="coerce")
        df["ltp_player_2"] = pd.to_numeric(df["ltp_player_2"], errors="coerce")
        # Avoid divide-by-zero
        df["implied_prob_1"] = 1 / df["ltp_player_1"].replace(0, np.nan)
        df["implied_prob_2"] = 1 / df["ltp_player_2"].replace(0, np.nan)
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]

        logging.info(
            "✅ Added implied_prob_1, implied_prob_2, implied_prob_diff, and odds_margin columns."
        )
    else:
        # Create the columns as all-NaN if missing
        for col in [
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ]:
            df[col] = np.nan
        logging.warning(
            "⚠️ ltp_player_1 or ltp_player_2 not found. Created implied prob columns as all-NaN."
        )

    # Warn if NaNs
    if ("implied_prob_1" in df.columns and df["implied_prob_1"].isnull().any()) or (
        "implied_prob_2" in df.columns and df["implied_prob_2"].isnull().any()
    ):
        logging.warning(
            "⚠️ Some implied probabilities are NaN (possibly due to missing or zero LTPs)."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"✅ Saved odds features to {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Build odds features from match/odds CSV"
    )
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    build_odds_features(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
