import pandas as pd

df = pd.read_csv("data/processed/ausopen_2023_atp_features.csv")
print(df.columns)
print(df[["ltp_player_1", "ltp_player_2"]].head())
if "implied_prob_1" in df.columns:
    print(
        df[
            ["implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"]
        ].head()
    )
else:
    print("No implied prob columns present.")
