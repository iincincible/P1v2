import pandas as pd

df = pd.read_csv("data/processed/merged_ausopen_2023_deduped.csv")
print(f"Total rows: {len(df)}")
print("Missing values per column:")
print(df[["odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff", "won"]].isna().sum())
