import pandas as pd
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True, help="Match file with selection_id_1/2 and market_id")
    parser.add_argument("--snapshots_csv", required=True, help="Snapshot file with latest selection_id-level LTPs")
    parser.add_argument("--output_csv", required=True, help="Where to save the filtered match file")
    args = parser.parse_args()

    # Load and normalize snapshots
    snaps = pd.read_csv(args.snapshots_csv, usecols=["market_id", "selection_id", "timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64").astype(str)
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"], errors="coerce")

    snaps = snaps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
    valid_keys = set(zip(snaps["market_id"], snaps["selection_id"]))

    # Load and normalize match file
    match_df = pd.read_csv(args.match_csv)
    match_df["market_id"] = match_df["market_id"].astype(str)
    match_df["selection_id_1"] = pd.to_numeric(match_df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
    match_df["selection_id_2"] = pd.to_numeric(match_df["selection_id_2"], errors="coerce").astype("Int64").astype(str)

    # Filter to rows where both player selection IDs exist in the snapshot data
    filtered_df = match_df[
        match_df.apply(
            lambda row: (row["market_id"], row["selection_id_1"]) in valid_keys and
                        (row["market_id"], row["selection_id_2"]) in valid_keys,
            axis=1
        )
    ]

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(filtered_df)} rows with valid snapshot coverage to {args.output_csv}")

if __name__ == "__main__":
    main()
