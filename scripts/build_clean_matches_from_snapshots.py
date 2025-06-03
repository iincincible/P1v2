import pandas as pd

# Load enriched match file
sackmann_path = "data/processed/ausopen_2023_merged.csv"
sackmann_df = pd.read_csv(sackmann_path, low_memory=False)

# Load valid AO market_ids
valid_ids_path = "parsed/valid_ao2023_market_ids.csv"
valid_ids = pd.read_csv(valid_ids_path)["market_id"].astype(str).tolist()
print(f"✅ Loaded {len(valid_ids)} valid AO 2023 market IDs")

# Filter Sackmann to those market_ids
sackmann_df["market_id"] = sackmann_df["market_id"].astype(str)
sackmann_df = sackmann_df[sackmann_df["market_id"].isin(valid_ids)]

# Load snapshots
snapshots_path = "parsed/betfair_tennis_snapshots.csv"
snapshots_df = pd.read_csv(snapshots_path, low_memory=False)
snapshots_df["selection_id"] = pd.to_numeric(snapshots_df["selection_id"], errors="coerce").astype("Int64").astype(str)
snapshots_df["market_id"] = snapshots_df["market_id"].astype(str)
snapshots_df["timestamp"] = pd.to_datetime(snapshots_df["timestamp"], errors="coerce")
snapshots_df = snapshots_df.dropna(subset=["ltp", "runner_name"])

# ✅ Filter to just the AO market_ids
snapshots_df = snapshots_df[snapshots_df["market_id"].isin(valid_ids)]

# ✅ Keep latest snapshot per runner (even if not final tick)
snapshots_df = snapshots_df.sort_values("timestamp")
snapshots_df = snapshots_df.drop_duplicates(["market_id", "selection_id"], keep="last")

# Build map of runners per market
runner_map = snapshots_df.groupby("market_id").apply(
    lambda grp: {
        "runners": list(grp.sort_values("selection_id")["runner_name"]),
        "odds": list(grp.sort_values("selection_id")["ltp"]),
        "selection_ids": list(grp.sort_values("selection_id")["selection_id"])
    }
).to_dict()

# Reconstruct player_1/player_2 and odds
clean_rows = []
for _, row in sackmann_df.iterrows():
    market_id = str(row.get("market_id"))
    if market_id not in runner_map:
        continue

    mapping = runner_map[market_id]
    if len(mapping["runners"]) != 2:
        continue

    player_1 = mapping["runners"][0]
    player_2 = mapping["runners"][1]
    odds_player_1 = mapping["odds"][0]
    odds_player_2 = mapping["odds"][1]

    clean_rows.append({
        **row.to_dict(),
        "player_1": player_1,
        "player_2": player_2,
        "odds_player_1": odds_player_1,
        "odds_player_2": odds_player_2,
    })

# Save results
out_df = pd.DataFrame(clean_rows)
out_path = "data/processed/ausopen_2023_clean_snapshot_matches.csv"
print(f"✅ Matched {len(out_df)} rows with available LTPs from AO 2023")
out_df.to_csv(out_path, index=False)
print(f"📁 Saved to {out_path}")
