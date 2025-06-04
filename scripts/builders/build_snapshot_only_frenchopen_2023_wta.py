import pandas as pd

# Load snapshot data
snap = pd.read_csv("parsed/betfair_tennis_snapshots_frenchopen2023_wta.csv", low_memory=False)
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")

# Drop rows without runner name or LTP
snap = snap.dropna(subset=["runner_name", "ltp"])

# Keep only latest LTP per (market_id, runner_name)
latest = snap.sort_values("timestamp").groupby(["market_id", "runner_name"], as_index=False).last()

# Optional: Sort players alphabetically within each market
def extract_ordered_market(row):
    runners = row.sort_values("runner_name")
    names = runners["runner_name"].values
    odds = runners["ltp"].values
    if len(names) != 2:
        return None  # skip incomplete markets
    return pd.Series({
        "player_1": names[0],
        "player_2": names[1],
        "odds_player_1": odds[0],
        "odds_player_2": odds[1]
    })

# Group by market and extract 2-player rows
grouped = latest.groupby("market_id")
rows = grouped.apply(extract_ordered_market).dropna().reset_index()

# Save
rows.to_csv("data/processed/frenchopen_2023_wta_snapshot_only.csv", index=False)
print(f"✅ Saved {len(rows)} snapshot-only WTA French Open matches to data/processed/frenchopen_2023_wta_snapshot_only.csv")
