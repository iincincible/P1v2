import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli_utils import should_run, add_common_flags
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.logger import log_info, log_success


def main():
    parser = argparse.ArgumentParser(description="Build implied odds features and EV/Kelly fields.")
    parser.add_argument("--input_csv", required=True, help="Path to input CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save output with features")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    df = pd.read_csv(args.input_csv)

    # === Flexible LTP handling ===
    if "odds_player_1" not in df.columns:
        if "ltp_player_1" in df.columns:
            df["odds_player_1"] = df["ltp_player_1"]
            log_info("🔧 Mapped ltp_player_1 → odds_player_1")
        elif "odds" in df.columns:
            df["odds_player_1"] = df["odds"]
            log_info("🔧 Used odds → odds_player_1")

    if "odds_player_2" not in df.columns:
        if "ltp_player_2" in df.columns:
            df["odds_player_2"] = df["ltp_player_2"]
            log_info("🔧 Mapped ltp_player_2 → odds_player_2")

    # === Compute implied probabilities ===
    if "implied_prob_1" not in df.columns and "odds_player_1" in df.columns:
        df["implied_prob_1"] = 1 / df["odds_player_1"]
    if "implied_prob_2" not in df.columns and "odds_player_2" in df.columns:
        df["implied_prob_2"] = 1 / df["odds_player_2"]

    if "odds_margin" not in df.columns and {"implied_prob_1", "implied_prob_2"}.issubset(df.columns):
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1

    if "implied_prob_diff" not in df.columns and {"implied_prob_1", "implied_prob_2"}.issubset(df.columns):
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    df = normalize_columns(df)
    if "predicted_prob" in df.columns:
        df = add_ev_and_kelly(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_success(f"✅ Saved odds features to {output_path}")


if __name__ == "__main__":
    main()
