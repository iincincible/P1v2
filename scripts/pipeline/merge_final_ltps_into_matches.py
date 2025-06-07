import argparse
import pandas as pd
from tqdm import tqdm
import os

from scripts.utils.cli_utils import should_run

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

    df_matches = pd.read_csv(args.match_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)

    df_snaps["market_id"] = df_snaps["market_id"].astype(str)
    df_snaps["selection_id"] = df_snaps["selection_id"].astype(str)

    snapshots_map = df_snaps.groupby(["market_id", "selection_id"]).last()["ltp"].to_dict()

    odds_1 = []
    odds_2 = []
    missing = 0

    for _, row in tqdm(df_matches.iterrows(), total=len(df_matches), desc="Merging LTPs"):
        m_id = str(row["market_id"])
        sel1 = str(row.get("selection_id_1", ""))
        sel2 = str(row.get("selection_id_2", ""))
        o1 = snapshots_map.get((m_id, sel1))
        o2 = snapshots_map.get((m_id, sel2))
        if pd.isna(o1) or pd.isna(o2):
            missing += 1
        odds_1.append(o1)
        odds_2.append(o2)

    df_matches["odds_player_1"] = odds_1
    df_matches["odds_player_2"] = odds_2

    print(f"✅ Matched {len(df_matches) - missing} LTP entries; unmatched {missing}")
    df_matches.to_csv(args.output_csv, index=False)
    print(f"✅ Saved merged odds to {args.output_csv}")

if __name__ == "__main__":
    main()
