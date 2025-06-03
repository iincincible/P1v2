import pandas as pd

# ✅ Use the merged Sackmann + snapshot metadata file
matches = pd.read_csv("data/processed/wta_merged_2023.csv", low_memory=False)
matches["market_id"] = matches["market_id"].astype(str)

# ✅ Load valid WTA AO 2023 market IDs
valid_ids = pd.read_csv("parsed/valid_ao2023_wta_market_ids.csv")["market_id"].astype(str).tolist()
matches = matches[matches["market_id"].isin(valid_ids)]

# ✅ Load snapshot file
snap = pd.read_csv("parsed/betfair_tennis_snapshots.csv", low_memory=False)
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")
snap = snap.dropna(subset=["ltp", "runner_name"])

# ✅ Get latest snapshot per runner
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# ✅ Create map of market_id → (runners + odds)
runner_map = snap.groupby("market_id").apply(
    lambda g: {
        "runners": list(g.sort_values("selection_id")["runner_name"]),
        "odds": list(g.sort_values("selection_id")["ltp"]),
    }
).to_dict()

# ✅ Reconstruct clean matches
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

# ✅ Save output
df_out = pd.DataFrame(clean_rows)
out_path = "data/processed/ausopen_2023_wta_clean_snapshot_matches.csv"
df_out.to_csv(out_path, index=False)
print(f"✅ Saved {len(df_out)} WTA AO 2023 clean matches to {out_path}")
