import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True, help="Merged match file with market_id")
    parser.add_argument("--snapshot_csv", required=True, help="Full snapshot file to filter")
    parser.add_argument("--output_csv", required=True, help="Where to save filtered snapshot file")
    args = parser.parse_args()

    print(f"🔍 Loading match file: {args.match_csv}")
    match_df = pd.read_csv(args.match_csv, usecols=["market_id"])
    market_ids = match_df["market_id"].dropna().astype(str).unique()
    print(f"✅ Found {len(market_ids)} unique market_ids")

    print(f"🔍 Loading snapshot file: {args.snapshot_csv}")
    snap_df = pd.read_csv(args.snapshot_csv, low_memory=False)
    snap_df["market_id"] = snap_df["market_id"].astype(str)

    print("🔁 Filtering snapshots...")
    filtered = snap_df[snap_df["market_id"].isin(market_ids)]
    print(f"✅ Retained {len(filtered)} rows across {filtered['market_id'].nunique()} markets")

    filtered.to_csv(args.output_csv, index=False)
    print(f"📁 Saved filtered snapshots to {args.output_csv}")

if __name__ == "__main__":
    main()
