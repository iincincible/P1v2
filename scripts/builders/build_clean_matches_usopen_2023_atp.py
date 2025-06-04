import pandas as pd

merged_path = "data/processed/merged_usopen_2023_patched.csv"
output_path = "data/processed/usopen_2023_atp_clean_snapshot_matches.csv"

print(f"📂 Loading: {merged_path}")
df = pd.read_csv(merged_path)

# Drop rows without valid odds
df = df.dropna(subset=["player_1", "player_2", "ltp_player_1", "ltp_player_2"])

# Convert LTPs to numeric odds
df["odds_player_1"] = pd.to_numeric(df["ltp_player_1"], errors="coerce")
df["odds_player_2"] = pd.to_numeric(df["ltp_player_2"], errors="coerce")

# Save final cleaned file
df.to_csv(output_path, index=False)
print(f"✅ Saved {len(df)} US Open ATP matches to {output_path}")
