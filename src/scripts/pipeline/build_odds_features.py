import argparse
import pandas as pd
import logging
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import add_common_flags, output_file_guard
from scripts.utils.normalize_columns import enforce_canonical_columns

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)


@output_file_guard(output_arg="output_csv")
def build_odds_features(
    input_csv,
    output_csv,
    overwrite=False,
    dry_run=False,
):
    df = pd.read_csv(input_csv)
    log_info(f"Loaded {len(df)} rows from {input_csv}")

    # =============== BEGIN YOUR CUSTOM FEATURE LOGIC ===============
    # Example: Always create 'odds' column if missing
    if "odds" not in df.columns:
        if "odds_player_1" in df.columns:
            df["odds"] = df["odds_player_1"]
            log_info("🔧 Created 'odds' column from 'odds_player_1'")
        elif "odds_player_2" in df.columns:
            df["odds"] = df["odds_player_2"]
            log_info("🔧 Created 'odds' column from 'odds_player_2'")
        else:
            log_warning("No odds source found! 'odds' column missing in features.")

    # Refactor: Enforce canonical columns at output
    try:
        enforce_canonical_columns(df, context="odds features")
    except Exception as e:
        log_warning(f"Canonical column check failed: {e}")

    df.to_csv(output_csv, index=False)
    log_success(f"✅ Saved odds features to {output_csv}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Build odds features for match predictions."
    )
    parser.add_argument("--input_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    add_common_flags(parser)
    _args = parser.parse_args(args)
    build_odds_features(
        input_csv=_args.input_csv,
        output_csv=_args.output_csv,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )


if __name__ == "__main__":
    main()
