import pandas as pd
from pathlib import Path

# Load Sackmann WTA Wimbledon 2023 results
sack_path = "data/raw/wimbledon_2023.csv"
df = pd.read_csv(sack_path)

# Filter to only WTA matches
df = df[df["tourney_name"].str.contains("Wimbledon", case=False)]
df = df[df["match_num"].notnull()]  # Ensure it's not walkovers or mislabelled rows

# Standardize date and player columns
df["match_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d").dt.date
df["player_1"] = df["winner_name"].str.upper().str.strip()
df["player_2"] = df["loser_name"].str.upper().str.strip()

# Keep only relevant columns
out = df[["match_date", "player_1", "player_2"]].dropna().drop_duplicates()

# Save
Path("parsed").mkdir(exist_ok=True)
out.to_csv("parsed/wimbledon_2023_wta_matches.csv", index=False)
print(f"✅ Saved {len(out)} Wimbledon WTA matches to parsed/wimbledon_2023_wta_matches.csv")
