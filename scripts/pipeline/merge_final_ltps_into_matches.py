import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    df = pd.read_csv(args.match_csv)
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.sort_values("timestamp")
    final_snaps = snaps.drop_duplicates(["market_id", "selection_id"], keep="last")

    snap_map = final_snaps.set_index(["market_id", "selection_id"])["ltp"].to_dict()

    df["ltp_player_1"] = df.apply(
        lambda row: snap_map.get((str(row["market_id"]), row["selection_id_1"])), axis=1
    )
    df["ltp_player_2"] = df.apply(
        lambda row: snap_map.get((str(row["market_id"]), row["selection_id_2"])), axis=1
    )

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved merged LTPs to {args.output_csv}")

if __name__ == "__main__":
    main()
