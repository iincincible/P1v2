import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_error, log_dryrun
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.normalize_columns import normalize_columns


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Build implied odds features and EV/Kelly fields."
    )
    parser.add_argument("--input_csv", required=True, help="Input CSV path")
    parser.add_argument(
        "--output_csv", required=True, help="Path to save output with features"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would build odds features from {_args.input_csv} → {_args.output_csv}"
        )
        return

    input_path = Path(_args.input_csv)
    output_path = Path(_args.output_csv)
    assert_file_exists(input_path, "input_csv")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        df = pd.read_csv(input_path)
        log_info(f"📥 Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        log_error(f"❌ Failed to read {input_path}: {e}")
        return

    # Flexible odds mapping
    if "odds_player_1" not in df.columns:
        if "ltp_player_1" in df.columns:
            df["odds_player_1"] = df["ltp_player_1"]
            log_info("🔧 Mapped ltp_player_1 → odds_player_1")
        elif "odds" in df.columns:
            df["odds_player_1"] = df["odds"]
            log_info("🔧 Mapped odds → odds_player_1")

    if "odds_player_2" not in df.columns and "ltp_player_2" in df.columns:
        df["odds_player_2"] = df["ltp_player_2"]
        log_info("🔧 Mapped ltp_player_2 → odds_player_2")

    # Compute implied probabilities & margins
    if "implied_prob_1" not in df.columns and "odds_player_1" in df.columns:
        df["implied_prob_1"] = 1 / df["odds_player_1"]
    if "implied_prob_2" not in df.columns and "odds_player_2" in df.columns:
        df["implied_prob_2"] = 1 / df["odds_player_2"]
    if "odds_margin" not in df.columns and {
        "implied_prob_1",
        "implied_prob_2",
    }.issubset(df.columns):
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    if "implied_prob_diff" not in df.columns and {
        "implied_prob_1",
        "implied_prob_2",
    }.issubset(df.columns):
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    # Normalize and add EV/Kelly
    df = normalize_columns(df)
    if "predicted_prob" in df.columns:
        try:
            df = add_ev_and_kelly(df)
        except Exception as e:
            log_error(f"❌ Failed to compute EV/Kelly: {e}")
            return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"✅ Saved odds features to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save odds features: {e}")


if __name__ == "__main__":
    main()
