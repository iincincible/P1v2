import pandas as pd
import argparse

def main(merged_csv, snapshots_csv, output_csv):
    df = pd.read_csv(merged_csv)
    snaps = pd.read_csv(snapshots_csv)

    # Get unique market_ids from snapshot data
    snapshot_market_ids = set(snaps["market_id"].unique())

    # Filter merged data to keep only those with snapshot coverage
    filtered = df[df["market_id"].isin(snapshot_market_ids)]

    print(f"✅ Filtered: {len(df)} → {len(filtered)} rows with snapshot coverage")
    filtered.to_csv(output_csv, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    main(args.merged_csv, args.snapshots_csv, args.output_csv)
