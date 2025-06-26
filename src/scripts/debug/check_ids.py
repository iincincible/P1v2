import pandas as pd

df = pd.read_csv("data/processed/ausopen_2023_atp_ids.csv")
print(df.columns)
print(df["selection_id_1"].head(10))
print("Unique types in selection_id_1:", df["selection_id_1"].apply(type).unique())
