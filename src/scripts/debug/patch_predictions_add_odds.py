import pandas as pd

# File paths
input_csv = "data/processed/ausopen_2023_atp_predictions.csv"
output_csv = "data/processed/ausopen_2023_atp_predictions_withodds.csv"

# Load predictions
df = pd.read_csv(input_csv)

# Add 'odds' column based on 'ltp_player_1'
# If you want to use ltp_player_2 instead, change the column below!
df["odds"] = df["ltp_player_1"]

# Optional: print how many odds are missing (NaN)
missing = df["odds"].isna().sum()
print(
    f"Added 'odds' column (from ltp_player_1). Missing odds: {missing} / {len(df)} rows."
)

# Save to new file
df.to_csv(output_csv, index=False)
print(f"✅ Patched predictions saved to: {output_csv}")
