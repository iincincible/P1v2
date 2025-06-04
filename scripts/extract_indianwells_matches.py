import pandas as pd
from pathlib import Path

# === Inputs ===
input_path = "data/tennis_atp/atp_matches_2023.csv"
output_path = "parsed/indianwells_2023_atp_matches.csv"

# === Load Sackmann ATP match data ===
df = pd.read_csv(input_path, low_memory=False)

# === Filter for Indian Wells ATP matches ===
df["tourney_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d")
iw = df[
    (df["tourney_name"] == "Indian Wells Masters") &
    (df["tourney_date"] >= "2023-03-06") &
    (df["tourney_date"] <= "2023-03-19")
].copy()

# === Add clean match_date for alignment
iw["match_date"] = iw["tourney_date"].dt.date

# === Save to parsed folder
Path("parsed").mkdir(exist_ok=True)
iw.to_csv(output_path, index=False)
print(f"✅ Saved {len(iw)} Indian Wells ATP matches to {output_path}")
