import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    df = pd.read_csv(args.merged_csv)
    snap = pd.read_csv(args.snapshots_csv)

    snap = snap.dropna(subset=["market_id", "selection_id", "runner_name", "ltp"])
    snap = snap.sort_values("timestamp")
    latest_snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

    runner_map = latest_snap.set_index(["market_id", "runner_name"])["selection_id"].to_dict()

    df["selection_id_1"] = df.apply(lambda row: runner_map.get((str(row["market_id"]), row["player_1"])), axis=1)
    df["selection_id_2"] = df.apply(lambda row: runner_map.get((str(row["market_id"]), row["player_2"])), axis=1)

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved match file with selection_ids: {args.output_csv}")

if __name__ == "__main__":
    main()
