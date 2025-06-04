import pandas as pd

merged = pd.read_csv("data/processed/merged_ausopen_2023.csv")
snaps = pd.read_csv("parsed/betfair_tennis_snapshots.csv")
ltps = pd.read_csv("parsed/final_ltps_per_runner.csv")

print("🔍 Columns in merged file:")
print(list(merged.columns))

print("\n🔍 Sample rows from merged:")
print(merged[["market_id", "player_1", "player_2"]].head(3))

print("\n🔍 Columns in snapshots:")
print(list(snaps.columns))

# Check for matching market_id + runner_1
runner_matches = snaps[["market_id", "runner_1", "selection_id"]].drop_duplicates()
merged_sample = merged.merge(
    runner_matches.rename(columns={"runner_1": "player_1", "selection_id": "selection_id_1"}),
    on=["market_id", "player_1"],
    how="left"
)

print("\n🧪 Join preview:")
print(merged_sample[["market_id", "player_1", "selection_id_1"]].head(5))

missing_count = merged_sample["selection_id_1"].isna().sum()
print(f"\n❌ Unmatched selection_id_1 rows: {missing_count} of {len(merged_sample)}")
