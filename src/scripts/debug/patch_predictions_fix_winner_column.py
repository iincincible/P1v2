import pandas as pd

file = "data/processed/ausopen_2023_atp_predictions_withodds.csv"

df = pd.read_csv(file)

# Print column info
print("\n=== Columns ===")
print(list(df.columns))
print("\n=== Sample player_1 and actual_winner ===")
print(df[["player_1", "actual_winner"]].head())

# Force columns to string type just in case
df["player_1"] = df["player_1"].astype(str)
df["actual_winner"] = df["actual_winner"].astype(str)

# Remove duplicate columns (like player_1.1, actual_winner.1)
for col in ["player_1.1", "actual_winner.1"]:
    if col in df.columns:
        print(f"Removing duplicate column: {col}")
        df = df.drop(columns=[col])

# Try to create 'winner' column
try:
    df["winner"] = (df["actual_winner"] == df["player_1"]).astype(int)
    print("\n✅ 'winner' column created. Sample:")
    print(df[["player_1", "actual_winner", "winner"]].head())
except Exception as e:
    print("\n❌ Error creating 'winner' column:", e)

# Save file
df.to_csv(file, index=False)
print(f"\n✅ File patched and saved: {file}")
