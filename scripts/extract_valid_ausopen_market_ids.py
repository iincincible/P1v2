import pandas as pd

df = pd.read_csv("parsed/market_metadata.csv")
hits = df[
    df["runner_1"].str.contains("DJOKOVIC|TSITSIPAS|RUBLEV|KHACHANOV|PAUL", case=False, na=False) |
    df["runner_2"].str.contains("DJOKOVIC|TSITSIPAS|RUBLEV|KHACHANOV|PAUL", case=False, na=False)
]
hits = hits[["market_id"]].drop_duplicates()
hits.to_csv("parsed/valid_ao2023_market_ids.csv", index=False)
print(f"✅ Saved {len(hits)} valid AO market_ids to parsed/valid_ao2023_market_ids.csv")
