import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path

from scripts.utils.selection import build_market_runner_map, match_player_to_selection_id
from scripts.utils.logger import log_info, log_warning, log_error, log_success
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags


def main():
    parser = argparse.ArgumentParser(description="Match player names to Betfair selection IDs.")
    parser.add_argument("--merged_csv", required=True, help="Input match CSV with player names")
    parser.add_argument("--snapshots_csv", required=True, help="Parsed Betfair snapshots")
    parser.add_argument("--output_csv", required=True, help="Path to save selection ID mapping")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.merged_csv, "merged_csv")
    assert_file_exists(args.snapshots_csv, "snapshots_csv")

    df_matches = pd.read_csv(args.merged_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)

    if "match_id" not in df_matches.columns:
        raise ValueError("❌ 'match_id' column is required in merged_csv")

    log_info(f"🔍 Matching selection IDs for {len(df_matches)} matches")

    market_runner_map = build_market_runner_map(df_snaps)

    tqdm.pandas()
    df_matches["selection_id_1"] = df_matches.progress_apply(
        lambda row: match_player_to_selection_id(market_runner_map, row["market_id"], row["player_1"]),
        axis=1
    )
    df_matches["selection_id_2"] = df_matches.progress_apply(
        lambda row: match_player_to_selection_id(market_runner_map, row["market_id"], row["player_2"]),
        axis=1
    )

    unmatched_1 = df_matches["selection_id_1"].isna().sum()
    unmatched_2 = df_matches["selection_id_2"].isna().sum()
    log_warning(f"⚠️ Unmatched selection_id_1: {unmatched_1}")
    log_warning(f"⚠️ Unmatched selection_id_2: {unmatched_2}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_matches.to_csv(output_path, index=False)
    log_success(f"✅ Saved selection ID mappings to {output_path}")


if __name__ == "__main__":
    main()
