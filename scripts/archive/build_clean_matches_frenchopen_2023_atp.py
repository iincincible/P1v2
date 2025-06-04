import pandas as pd

# Load merged ATP match metadata
merged_path = "data/processed/atp_merged_2023.csv"
matches = pd.read_csv(merged_path, low_memory=False)
matches["market_id"] = matches["market_id"].astype(str)

# Load valid Roland Garros market IDs
valid_ids = pd.read_csv("parsed/valid_frenchopen_2023_atp_market_ids.csv")["market_id"].astype(str).tolist()
matches = matches[matches["market_id"].isin(valid_ids)]

# Load Betfair snapshots
snap = pd.read_csv("parsed/betfair_tennis_snapshots.csv", low_memory=False)
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")
snap = snap.dropna(subset=["ltp", "runner_name"])

# Use latest available snapshot per runner
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# Build mapping of runners and odds per market
runner_map = snap.groupby("market_id").apply(
    lambda g: {
        "runners": list(g.sort_values("selection_id")["runner_name"]),
        "odds": list(g.sort_values("selection_id")["ltp"]),
    }
).to_dict()

# Build clean match rows
clean_rows = []
for _, row in matches.iterrows():
    mid = row["market_id"]
    if mid not in runner_map:
        continue
    m = runner_map[mid]
    if len(m["runners"]) != 2:
        continue
    clean_rows.append({
        **row,
        "player_1": m["runners"][0],
        "player_2": m["runners"][1],
        "odds_player_1": m["odds"][0],
        "odds_player_2": m["odds"][1],
    })

# Save result
df_out = pd.DataFrame(clean_rows)
out_path = "data/processed/frenchopen_2023_atp_clean_snapshot_matches.csv"
df_out.to_csv(out_path, index=False)
print(f"✅ Saved {len(df_out)} ATP French Open matches to {out_path}")
