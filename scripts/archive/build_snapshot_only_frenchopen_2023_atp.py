import pandas as pd

# Load market_ids for Roland Garros ATP
valid_ids = pd.read_csv("parsed/valid_frenchopen_2023_atp_market_ids.csv")["market_id"].astype(str).tolist()

# Load snapshots
snap = pd.read_csv("parsed/betfair_tennis_snapshots.csv", low_memory=False)
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")
snap = snap.dropna(subset=["ltp", "runner_name"])

# Filter to French Open markets
snap = snap[snap["market_id"].isin(valid_ids)]

# Keep latest snapshot per runner
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# ✅ Manually build runner map
runner_map = {}
for market_id, group in snap.groupby("market_id"):
    sorted_group = group.sort_values("selection_id")
    runners = list(sorted_group["runner_name"])
    odds = list(sorted_group["ltp"])
    if len(runners) == 2:
        runner_map[market_id] = {"runners": runners, "odds": odds}

# Build match rows
clean_rows = []
for market_id, data in runner_map.items():
    clean_rows.append({
        "market_id": market_id,
        "player_1": data["runners"][0],
        "player_2": data["runners"][1],
        "odds_player_1": data["odds"][0],
        "odds_player_2": data["odds"][1],
    })

# Save
df_out = pd.DataFrame(clean_rows)
out_path = "data/processed/frenchopen_2023_atp_snapshot_only.csv"
df_out.to_csv(out_path, index=False)
print(f"✅ Saved {len(df_out)} snapshot-only matches to {out_path}")
