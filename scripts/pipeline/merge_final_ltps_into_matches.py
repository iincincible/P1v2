import argparse
import pandas as pd
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import assert_file_exists, should_run, add_common_flags


def main():
    parser = argparse.ArgumentParser(description="Merge final LTPs from snapshots into matches CSV.")
    parser.add_argument("--matches_csv", required=True, help="Path to clean matches CSV")
    parser.add_argument("--snapshots_csv", required=True, help="Path to parsed Betfair snapshots")
    parser.add_argument("--output_csv", required=True, help="Path to save enriched matches CSV")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.matches_csv, "matches_csv")
    assert_file_exists(args.snapshots_csv, "snapshots_csv")

    matches = pd.read_csv(args.matches_csv)
    snapshots = pd.read_csv(args.snapshots_csv)

    if "market_id" not in matches.columns or "market_id" not in snapshots.columns:
        raise ValueError("❌ Both files must contain market_id column")

    # Get final LTPs per selection
    final_ltp = (
        snapshots
        .sort_values(by="timestamp")
        .groupby(["market_id", "selection_id"])
        .last()
        .reset_index()[["market_id", "selection_id", "ltp"]]
    )

    merged = matches.merge(final_ltp, left_on=["market_id", "selection_id_1"], right_on=["market_id", "selection_id"], how="left")
    merged = merged.rename(columns={"ltp": "ltp_player_1"}).drop(columns=["selection_id"])

    merged = merged.merge(final_ltp, left_on=["market_id", "selection_id_2"], right_on=["market_id", "selection_id"], how="left")
    merged = merged.rename(columns={"ltp": "ltp_player_2"}).drop(columns=["selection_id"])

    if merged["ltp_player_1"].isna().any() or merged["ltp_player_2"].isna().any():
        log_warning("⚠️ Some LTP values are missing after merge")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    log_success(f"✅ Saved matches with LTPs to {output_path}")


if __name__ == "__main__":
    main()
