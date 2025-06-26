import pandas as pd

df = pd.read_csv("data/processed/ausopen_2023_atp_with_odds.csv")
print(df.columns)
print(df[["ltp_player_1", "ltp_player_2"]].head(10))
print("\nTypes for ltp_player_1:", df["ltp_player_1"].apply(type).unique())
print("Types for ltp_player_2:", df["ltp_player_2"].apply(type).unique())
