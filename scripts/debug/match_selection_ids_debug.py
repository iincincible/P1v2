import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.merged_csv)
    snaps = pd.read_csv(args.snapshots_csv)

    snaps = snaps.dropna(subset=["market_id", "selection_id", "runner_name"])
    snaps["market_id"] = snaps["market_id"].astype(str).str.strip()
    snaps["runner_name"] = snaps["runner_name"].astype(str).str.lower().str.strip()

    snap_map = snaps.set_index(["market_id", "runner_name"])["selection_id"].to_dict()

    def get_selection_id(row, side):
        player_name = row[f"player_{side}"]
        if pd.isna(player_name):
            print(f"⚠️ Missing player_{side} name for market {row['market_id']}")
            return None
        key = (str(row["market_id"]), str(player_name).lower().strip())
        selection_id = snap_map.get(key)
        if selection_id is None:
            print(f"⚠️ Missing selection_id for market {key[0]}, player_{side} = {key[1]}")
        return selection_id

    df["selection_id_1"] = df.apply(lambda row: get_selection_id(row, 1), axis=1)
    df["selection_id_2"] = df.apply(lambda row: get_selection_id(row, 2), axis=1)

    missing_1 = df["selection_id_1"].isna().sum()
    missing_2 = df["selection_id_2"].isna().sum()
    print(f"Total missing selection_id_1: {missing_1}")
    print(f"Total missing selection_id_2: {missing_2}")

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved selection IDs to {args.output_csv}")

if __name__ == "__main__":
    main()
