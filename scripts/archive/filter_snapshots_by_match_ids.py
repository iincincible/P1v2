import pandas as pd
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    # Load repaired match file
    match_df = pd.read_csv(args.match_csv)
    match_df["market_id"] = match_df["market_id"].astype(str)

    # Extract valid market_ids
    valid_ids = match_df["market_id"].dropna().unique().tolist()

    # Load snapshot file
    snap_df = pd.read_csv(args.snapshots_csv)
    snap_df["market_id"] = snap_df["market_id"].astype(str)

    # Filter to matching market_ids
    filtered = snap_df[snap_df["market_id"].isin(valid_ids)].copy()
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(args.output_csv, index=False)

    print(f"✅ Filtered {len(filtered)} snapshot rows to {args.output_csv}")
    print(f"🧠 Kept {len(valid_ids)} unique market_ids")

if __name__ == "__main__":
    main()
