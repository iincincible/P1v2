import pandas as pd
import argparse
from tqdm import tqdm

def build_dataset(merged_csv, snapshots_csv, output_csv):
    print(f"🔍 Reading merged: {merged_csv}")
    merged = pd.read_csv(merged_csv)
    print(f"🔍 Reading snapshot data: {snapshots_csv}")
    snaps = pd.read_csv(snapshots_csv)

    # Drop incomplete rows
    merged = merged.dropna(subset=["market_id", "player_1", "player_2", "winner_name"])
    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp"])

    # Standardize player name columns for join
    merged["player_1_lc"] = merged["player_1"].str.lower().str.replace(".", "", regex=False).str.strip()
    merged["player_2_lc"] = merged["player_2"].str.lower().str.replace(".", "", regex=False).str.strip()
    snaps["runner_1_lc"] = snaps["runner_1"].str.lower().str.replace(".", "", regex=False).str.strip()
    snaps["runner_2_lc"] = snaps["runner_2"].str.lower().str.replace(".", "", regex=False).str.strip()

    selection_map = []

    print("🔁 Matching player_1 to selection_id_1")
    for _, row in tqdm(merged.iterrows(), total=len(merged)):
        snap = snaps[snaps["market_id"] == row["market_id"]]
        sid1 = None
        sid2 = None
        try:
            match1 = snap[snap["runner_1_lc"] == row["player_1_lc"]]
            match2 = snap[snap["runner_2_lc"] == row["player_2_lc"]]
            if not match1.empty and not match2.empty:
                sid1 = match1["selection_id"].values[0]
                sid2 = match2["selection_id"].values[0]
        except Exception:
            pass
        selection_map.append((sid1, sid2))

    merged["selection_id_1"] = [a for a, _ in selection_map]
    merged["selection_id_2"] = [b for _, b in selection_map]

    # Add LTPs as fallback odds
    print("🔁 Attaching LTPs as fallback odds")
    ltps = snaps[["market_id", "selection_id", "ltp"]].copy()
    ltps_1 = ltps.rename(columns={"selection_id": "selection_id_1", "ltp": "ltp_1"})
    ltps_2 = ltps.rename(columns={"selection_id": "selection_id_2", "ltp": "ltp_2"})

    merged = merged.merge(ltps_1, on=["market_id", "selection_id_1"], how="left")
    merged = merged.merge(ltps_2, on=["market_id", "selection_id_2"], how="left")

    # Create 'odds_player_1' and 'odds_player_2' with fallback to LTPs
    if "odds_player_1" not in merged.columns:
        merged["odds_player_1"] = merged["ltp_1"]
    else:
        merged["odds_player_1"] = merged["odds_player_1"].fillna(merged["ltp_1"])

    if "odds_player_2" not in merged.columns:
        merged["odds_player_2"] = merged["ltp_2"]
    else:
        merged["odds_player_2"] = merged["odds_player_2"].fillna(merged["ltp_2"])

    # Drop rows with missing final odds
    merged = merged.dropna(subset=["odds_player_1", "odds_player_2"])

    # Label winner
    merged["won"] = (merged["player_1"] == merged["winner_name"]).astype(int)

    print(f"✅ Final training set: {len(merged)} rows")
    merged.to_csv(output_csv, index=False)
    print(f"✅ Saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    build_dataset(args.merged_csv, args.snapshots_csv, args.output_csv)
