import pandas as pd
from pathlib import Path

# === Inputs ===
input_path = "data/tennis_wta/wta_matches_2023.csv"
output_path = "parsed/indianwells_2023_wta_matches.csv"

# === Load Sackmann WTA match data ===
df = pd.read_csv(input_path, low_memory=False)

# === Filter for Indian Wells WTA ===
df["tourney_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d")
iw = df[
    (df["tourney_name"].str.contains("Indian Wells", case=False)) &
    (df["tourney_date"] >= "2023-03-06") &
    (df["tourney_date"] <= "2023-03-19")
].copy()

# === Add match_date column
iw["match_date"] = iw["tourney_date"].dt.date

# === Save result
Path("parsed").mkdir(exist_ok=True)
iw.to_csv(output_path, index=False)
print(f"✅ Saved {len(iw)} Indian Wells WTA matches to {output_path}")
