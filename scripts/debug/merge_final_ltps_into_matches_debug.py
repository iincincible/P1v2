import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.match_csv)
    snaps = pd.read_csv(args.snapshots_csv)

    # Normalize market_id and selection_id to strings and strip whitespace
    snaps["market_id"] = snaps["market_id"].astype(str).str.strip()
    df["market_id"] = df["market_id"].astype(str).str.strip()
    snaps["selection_id"] = snaps["selection_id"].astype(str).str.strip()
    df["selection_id_1"] = df["selection_id_1"].astype(str).str.strip()
    df["selection_id_2"] = df["selection_id_2"].astype(str).str.strip()

    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp"])
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"], errors="coerce")
    snaps = snaps.sort_values("timestamp")
    final_snaps = snaps.drop_duplicates(["market_id", "selection_id"], keep="last")

    print(f"Sample market_id from matches file: {df['market_id'].head(5).tolist()}")
    print(f"Sample selection_id_1 from matches file: {df['selection_id_1'].head(5).tolist()}")
    print(f"Sample selection_id_2 from matches file: {df['selection_id_2'].head(5).tolist()}")
    print(f"Sample market_id from snapshots file: {final_snaps['market_id'].head(5).tolist()}")
    print(f"Sample selection_id from snapshots file: {final_snaps['selection_id'].head(5).tolist()}")

    snap_map = final_snaps.set_index(["market_id", "selection_id"])["ltp"].to_dict()

    matched = 0
    unmatched = 0

    def map_ltp(row, side):
        key = (row["market_id"], row[f"selection_id_{side}"])
        value = snap_map.get(key)
        nonlocal matched, unmatched
        if value is not None:
            matched += 1
        else:
            unmatched += 1
            print(f"⚠️ LTP missing for market {key[0]}, selection_id_{side} = {key[1]}")
        return value

    df["odds_player_1"] = df.apply(lambda row: map_ltp(row, 1), axis=1)
    df["odds_player_2"] = df.apply(lambda row: map_ltp(row, 2), axis=1)

    print(f"✅ Matched {matched} LTP entries; unmatched {unmatched}")

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved merged odds to {args.output_csv}")

if __name__ == "__main__":
    main()
