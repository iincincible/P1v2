import pandas as pd

df = pd.read_csv("data/processed/ausopen_2023_features_ready.csv")

def create_flipped_rows(row):
    flipped = row.copy()
    # Swap players
    flipped["player_1"], flipped["player_2"] = row["player_2"], row["player_1"]
    # Swap odds
    flipped["odds_player_1"], flipped["odds_player_2"] = row["odds_player_2"], row["odds_player_1"]
    # Flip label
    flipped["player_1_won"] = 1 - row["player_1_won"]
    return pd.DataFrame([row, flipped])

df_expanded = pd.concat(df.apply(create_flipped_rows, axis=1).to_list(), ignore_index=True)

print("Original rows:", len(df))
print("Expanded rows:", len(df_expanded))
print("Label distribution:\n", df_expanded["player_1_won"].value_counts())

df_expanded.to_csv("data/processed/ausopen_2023_features_expanded.csv", index=False)
print("Saved expanded balanced dataset.")
