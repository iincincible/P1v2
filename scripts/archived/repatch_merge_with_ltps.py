import pandas as pd
import argparse

def repatch_odds(merged_csv, snapshots_csv, ltps_csv, output_csv):
    merged = pd.read_csv(merged_csv)
    snaps = pd.read_csv(snapshots_csv)
    ltps = pd.read_csv(ltps_csv)

    # Deduplicate snapshot runner-to-selection mapping
    r1_map = snaps[["market_id", "runner_1", "selection_id"]].dropna().drop_duplicates()
    r2_map = snaps[["market_id", "runner_2", "selection_id"]].dropna().drop_duplicates()

    r1_map = r1_map.rename(columns={"runner_1": "player_1", "selection_id": "selection_id_1"})
    r2_map = r2_map.rename(columns={"runner_2": "player_2", "selection_id": "selection_id_2"})

    r1_map = r1_map.drop_duplicates(subset=["market_id", "player_1"])
    r2_map = r2_map.drop_duplicates(subset=["market_id", "player_2"])

    # Join to get selection_id_1 and _2
    merged = merged.merge(r1_map, on=["market_id", "player_1"], how="left")
    merged = merged.merge(r2_map, on=["market_id", "player_2"], how="left")

    # Pull final LTP odds
    ltp1 = ltps.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"})
    ltp2 = ltps.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"})

    merged = merged.merge(ltp1, on=["market_id", "selection_id_1"], how="left")
    merged = merged.merge(ltp2, on=["market_id", "selection_id_2"], how="left")

    # Drop selection ID columns for cleanliness
    merged = merged.drop(columns=["selection_id_1", "selection_id_2"], errors="ignore")

    merged.to_csv(output_csv, index=False)
    print(f"✅ Cleaned and repatched {len(merged)} rows → saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    repatch_odds(args.merged_csv, args.snapshots_csv, args.ltps_csv, args.output_csv)
