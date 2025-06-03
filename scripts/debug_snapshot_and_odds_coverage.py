import argparse
import pandas as pd

def debug_columns(df):
    print("🔎 Checking for missing values in key odds/probability columns:")
    for col in ["odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff", "won"]:
        if col in df.columns:
            missing = df[col].isna().sum()
            print(f"  - {col}: {missing} missing")
        else:
            print(f"  - {col}: ❌ Not found")

def debug_market_id_coverage(match_df, snapshot_df):
    match_ids = set(match_df["market_id"].dropna().astype(str).unique())
    snap_ids = set(snapshot_df["market_id"].dropna().astype(str).unique())
    intersection = match_ids & snap_ids
    print(f"\n📊 Market ID overlap: {len(intersection)} of {len(match_ids)} match file IDs found in snapshots")

def debug_selection_id_coverage(match_df, snapshot_df):
    # Normalize types
    match_df["market_id"] = match_df["market_id"].astype(str)
    match_df["selection_id_1"] = pd.to_numeric(match_df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
    match_df["selection_id_2"] = pd.to_numeric(match_df["selection_id_2"], errors="coerce").astype("Int64").astype(str)
    id_keys = set(zip(match_df["market_id"], match_df["selection_id_1"])) | set(zip(match_df["market_id"], match_df["selection_id_2"]))

    snapshot_df["market_id"] = snapshot_df["market_id"].astype(str)
    snapshot_df["selection_id"] = pd.to_numeric(snapshot_df["selection_id"], errors="coerce").astype("Int64").astype(str)
    snapshot_df["timestamp"] = pd.to_datetime(snapshot_df["timestamp"], errors="coerce")
    snapshot_df = snapshot_df.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
    ltp_keys = set(zip(snapshot_df["market_id"], snapshot_df["selection_id"]))

    matched = id_keys & ltp_keys
    print(f"🔁 Selection ID coverage: {len(matched)} of {len(id_keys)} matched with final snapshots")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True, help="Path to merged match file")
    parser.add_argument("--snapshot_csv", default="parsed/betfair_tennis_snapshots.csv", help="Path to snapshot CSV")
    args = parser.parse_args()

    print(f"\n📂 Loading: {args.match_csv}")
    match_df = pd.read_csv(args.match_csv, low_memory=False)
    snapshot_df = pd.read_csv(args.snapshot_csv, low_memory=False)

    print("\n🔍 Step 1: Column Null Check")
    debug_columns(match_df)

    print("\n🔍 Step 2: Market ID Overlap")
    debug_market_id_coverage(match_df, snapshot_df)

    if "selection_id_1" in match_df.columns and "selection_id_2" in match_df.columns:
        print("\n🔍 Step 3: Selection ID Match Coverage")
        debug_selection_id_coverage(match_df, snapshot_df)
    else:
        print("\n⚠️ Skipping selection ID match check — selection_id_1/2 not found in match file.")

if __name__ == "__main__":
    main()
