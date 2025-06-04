import pandas as pd
from pathlib import Path

# === INPUT ===
snapshot_path = "parsed/betfair_tennis_snapshots_iw2023_atp_filtered_strict.csv"
output_path = "data/processed/indianwells_2023_atp_clean_snapshot_matches.csv"

# === Load filtered snapshot file ===
snap = pd.read_csv(snapshot_path, low_memory=False)
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")

# Drop bad rows
snap = snap.dropna(subset=["ltp", "runner_name"])

# Keep latest snapshot per runner
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# === Build runner map (2-runner markets only) ===
runner_map = {}
for market_id, group in snap.groupby("market_id"):
    sorted_group = group.sort_values("selection_id")
    runners = list(sorted_group["runner_name"])
    odds = list(sorted_group["ltp"])
    if len(runners) == 2:
        runner_map[market_id] = {"runners": runners, "odds": odds}

# === Construct clean match rows ===
rows = []
for market_id, data in runner_map.items():
    rows.append({
        "market_id": market_id,
        "player_1": data["runners"][0],
        "player_2": data["runners"][1],
        "odds_player_1": data["odds"][0],
        "odds_player_2": data["odds"][1],
    })

# === Save output ===
df_out = pd.DataFrame(rows)
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(output_path, index=False)
print(f"✅ Saved {len(df_out)} clean matches to {output_path}")
