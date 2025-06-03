import pandas as pd
from difflib import get_close_matches
import argparse

def fuzzy_match_names(merged_df, snapshots_df):
    if "selection_name" not in snapshots_df.columns:
        raise ValueError("❌ The snapshots file must contain a 'selection_name' column to match against.")

    snapshot_lookup = (
        snapshots_df.dropna(subset=["market_id", "selection_id", "selection_name"])
        .groupby("market_id")["selection_name"]
        .unique()
        .to_dict()
    )

    repaired_names = []
    repaired_count = 0

    for idx, row in merged_df.iterrows():
        if pd.isna(row.get("selection_name")) and pd.notna(row.get("market_id")) and pd.notna(row.get("player_name")):
            candidates = snapshot_lookup.get(row["market_id"], [])
            matches = get_close_matches(row["player_name"], candidates, n=1, cutoff=0.7)
            if matches:
                repaired_names.append(matches[0])
                repaired_count += 1
            else:
                repaired_names.append(None)
        else:
            repaired_names.append(row.get("selection_name"))

    merged_df["selection_name"] = repaired_names
    print(f"✅ Repaired {repaired_count} missing selection_name entries using fuzzy matching.")
    return merged_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    merged_df = pd.read_csv(args.merged_csv)
    snapshots_df = pd.read_csv(args.snapshots_csv)

    if "selection_name" not in snapshots_df.columns:
        print("❌ Aborted: 'selection_name' column is missing in the snapshots file.")
    else:
        result_df = fuzzy_match_names(merged_df, snapshots_df)
        result_df.to_csv(args.output_csv, index=False)
        print(f"📁 Saved repaired file to: {args.output_csv}")
