import pandas as pd
import argparse
from pathlib import Path

def build_snapshot_only_matches(snapshots_csv, output_csv):
    snap = pd.read_csv(snapshots_csv)
    snap = snap.dropna(subset=["runner_name", "ltp", "market_id", "selection_id", "timestamp"])
    snap["timestamp"] = pd.to_datetime(snap["timestamp"])
    snap["market_id"] = snap["market_id"].astype(str)
    snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64")
    snap = snap.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    # Build 2-runner market map
    clean_rows = []
    for mid, group in snap.groupby("market_id"):
        g = group.sort_values("selection_id")
        if len(g) != 2:
            continue
        runners = list(g["runner_name"])
        odds = list(g["ltp"])
        clean_rows.append({
            "market_id": mid,
            "player_1": runners[0],
            "player_2": runners[1],
            "odds_player_1": odds[0],
            "odds_player_2": odds[1],
        })

    df_out = pd.DataFrame(clean_rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    print(f"✅ Saved {len(df_out)} snapshot-only matches to {output_csv}")

# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    build_snapshot_only_matches(args.snapshots_csv, args.output_csv)
