import argparse
import pandas as pd
from tqdm import tqdm
import os

from scripts.utils.cli_utils import should_run, assert_file_exists
from scripts.utils.selection import build_market_runner_map

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.match_csv, "match_csv")
    assert_file_exists(args.snapshots_csv, "snapshots_csv")

    df_matches = pd.read_csv(args.match_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)

    # Ensure consistent types
    df_snaps["market_id"] = df_snaps["market_id"].astype(str)
    df_snaps["selection_id"] = df_snaps["selection_id"].astype(str)

    market_runner_map = build_market_runner_map(df_snaps)

    odds_1 = []
    odds_2 = []
    missing = 0

    for _, row in tqdm(df_matches.iterrows(), total=len(df_matches), desc="Merging LTPs"):
        market_id = str(row["market_id"])
        sel1 = str(row.get("selection_id_1", ""))
        sel2 = str(row.get("selection_id_2", ""))
        market = market_runner_map.get(market_id, {})

        o1 = df_snaps.loc[
            (df_snaps["market_id"] == market_id) & (df_snaps["selection_id"] == sel1),
            "ltp"
        ].values
        o2 = df_snaps.loc[
            (df_snaps["market_id"] == market_id) & (df_snaps["selection_id"] == sel2),
            "ltp"
        ].values

        val1 = o1[0] if len(o1) else None
        val2 = o2[0] if len(o2) else None

        if pd.isna(val1) or pd.isna(val2):
            missing += 1
        odds_1.append(val1)
        odds_2.append(val2)

    df_matches["odds_player_1"] = odds_1
    df_matches["odds_player_2"] = odds_2

    print(f"✅ Matched {len(df_matches) - missing} LTP entries; unmatched {missing}")
    df_matches.to_csv(args.output_csv, index=False)
    print(f"✅ Saved merged odds to {args.output_csv}")

if __name__ == "__main__":
    main()
