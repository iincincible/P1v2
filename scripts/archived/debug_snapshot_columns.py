import pandas as pd

# Load the snapshot file
ltps = pd.read_csv("parsed/betfair_tennis_snapshots.csv")

# Print all column names
print("📄 Columns in snapshot file:")
for col in ltps.columns:
    print(f" - {col}")
