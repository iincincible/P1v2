import argparse
import pandas as pd
from difflib import get_close_matches
from collections import defaultdict
from tqdm import tqdm
import os

from scripts.utils.cli_utils import should_run

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    df = pd.read_csv(args.merged_csv)
    snapshots = pd.read_csv(args.snapshots_csv)

    print(f"🔍 Matching selection_ids for {len(df)} matches...")
    snapshots["runner_name_clean"] = snapshots["runner_name"].str.lower().str.strip()
    market_runner_map = defaultdict(dict)

    for _, row in snapshots.iterrows():
        market_runner_map[str(row["market_id"])][row["runner_name_clean"]] = row["selection_id"]

    def find_best_match(market_id, player_name):
        player_clean = str(player_name).lower().strip()
        candidates = list(market_runner_map.get(str(market_id), {}).keys())
        match = get_close_matches(player_clean, candidates, n=1, cutoff=0.8)
        return market_runner_map[str(market_id)].get(match[0]) if match else None

    tqdm.pandas()
    df["selection_id_1"] = df.progress_apply(lambda row: find_best_match(row["market_id"], row["player_1"]), axis=1)
    df["selection_id_2"] = df.progress_apply(lambda row: find_best_match(row["market_id"], row["player_2"]), axis=1)

    unmatched_1 = df["selection_id_1"].isna().sum()
    unmatched_2 = df["selection_id_2"].isna().sum()
    print(f"⚠️ Unmatched selection_id_1: {unmatched_1}")
    print(f"⚠️ Unmatched selection_id_2: {unmatched_2}")

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved selection IDs to {args.output_csv}")

if __name__ == "__main__":
    main()
