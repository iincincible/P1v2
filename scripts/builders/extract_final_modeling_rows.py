import pandas as pd

# Load Betfair snapshots and reduce to final snapshot per runner
ltps = pd.read_csv("parsed/betfair_tennis_snapshots.csv", usecols=["market_id", "selection_id", "timestamp"])
ltps["selection_id"] = pd.to_numeric(ltps["selection_id"], errors="coerce").astype("Int64").astype(str)
ltps["market_id"] = ltps["market_id"].astype(str)
ltps["timestamp"] = pd.to_datetime(ltps["timestamp"], errors="coerce")

ltps = ltps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
valid_keys = set(zip(ltps["market_id"], ltps["selection_id"]))

# Load clean match-aligned rows (player_1/player_2 already matched to runner_1/runner_2)
df = pd.read_csv("data/processed/ausopen_2023_clean_snapshot_matches.csv", low_memory=False)
df["selection_id_1"] = pd.to_numeric(df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
df["selection_id_2"] = pd.to_numeric(df["selection_id_2"], errors="coerce").astype("Int64").astype(str)
df["market_id"] = df["market_id"].astype(str)

# Filter only rows where both player selection IDs exist in snapshot data
df_filtered = df[
    df.apply(
        lambda row: (row["market_id"], row["selection_id_1"]) in valid_keys and
                    (row["market_id"], row["selection_id_2"]) in valid_keys,
        axis=1
    )
]

df_filtered.to_csv("data/processed/ausopen_2023_final_for_modeling.csv", index=False)
print(f"✅ Saved {len(df_filtered)} fully matchable rows with valid LTPs for modeling.")
