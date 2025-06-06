import pandas as pd

# Load match file
df = pd.read_csv("data/processed/ausopen_2023_ids.csv")
df["selection_id_1"] = pd.to_numeric(df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
df["selection_id_2"] = pd.to_numeric(df["selection_id_2"], errors="coerce").astype("Int64").astype(str)
df["market_id"] = df["market_id"].astype(str)

id_keys = set(zip(df["market_id"], df["selection_id_1"])) | set(zip(df["market_id"], df["selection_id_2"]))
print(f"🔎 Unique ID keys in match file: {len(id_keys):,}")

# Load snapshot LTPs
snap = pd.read_csv("parsed/betfair_tennis_snapshots.csv", usecols=["market_id", "selection_id", "timestamp"])
snap["market_id"] = snap["market_id"].astype(str)
snap["selection_id"] = pd.to_numeric(snap["selection_id"], errors="coerce").astype("Int64").astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")

snap = snap.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
ltp_keys = set(zip(snap["market_id"], snap["selection_id"]))
print(f"✅ Final LTP keys: {len(ltp_keys):,}")

# Compare
matched = id_keys & ltp_keys
print(f"✅ Matches between match file and snapshots: {len(matched):,}")
