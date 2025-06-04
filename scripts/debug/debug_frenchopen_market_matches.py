import pandas as pd

# Load merged ATP match data
merged = pd.read_csv("data/processed/atp_merged_2023.csv", low_memory=False)
merged["market_id"] = merged["market_id"].astype(str)

# Load Roland Garros market_ids
valid_ids = pd.read_csv("parsed/valid_frenchopen_2023_atp_market_ids.csv")["market_id"].astype(str).tolist()

# How many match rows use those market_ids?
merged_subset = merged[merged["market_id"].isin(valid_ids)]
print(f"✅ Matched {len(merged_subset)} merged rows for French Open market_ids")

# Load snapshots and get final LTP snapshot per runner
snap = pd.read_csv("parsed/betfair_tennis_snapshots.csv", low_memory=False)
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")
snap = snap.dropna(subset=["ltp", "runner_name"])
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# How many of the French Open market_ids exist in the final snapshots?
snap_ids = set(snap["market_id"].unique())
merged_ids = set(merged_subset["market_id"].unique())
shared_ids = snap_ids & merged_ids
print(f"✅ {len(shared_ids)} of {len(merged_ids)} market_ids found in final snapshot data")
