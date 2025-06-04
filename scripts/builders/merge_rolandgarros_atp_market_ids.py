import pandas as pd

# Dates you want to combine
dates = ["2023-05-29", "2023-05-30", "2023-05-31"]

# Load master ATP market file
df = pd.read_csv("parsed/betfair_atp_markets_2023.csv", parse_dates=["market_time"])
df["date"] = df["market_time"].dt.date.astype(str)

# Filter to selected days
df_filtered = df[df["date"].isin(dates)]
out = df_filtered[["market_id"]].drop_duplicates()

# Save
out_path = "parsed/valid_frenchopen_2023_atp_market_ids.csv"
out.to_csv(out_path, index=False)
print(f"✅ Merged {len(out)} market_ids from {dates} into {out_path}")
