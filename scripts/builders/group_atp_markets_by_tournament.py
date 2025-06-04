import pandas as pd
from pathlib import Path

# Load metadata
df = pd.read_csv("parsed/betfair_atp_markets_2023.csv", parse_dates=["market_time"])

# Extract date only
df["date"] = df["market_time"].dt.date

# Normalize player names
def clean_name(x):
    return str(x).strip().upper()

df["runner_1_clean"] = df["runner_1"].map(clean_name)
df["runner_2_clean"] = df["runner_2"].map(clean_name)

# Group by day and get unique player counts
grouped = (
    df.groupby("date")
    .agg(
        num_markets=("market_id", "nunique"),
        unique_runners=("runner_1_clean", lambda x: len(set(x)) + len(set(df.loc[x.index, "runner_2_clean"])))
    )
    .reset_index()
    .sort_values("unique_runners", ascending=False)
)

# Save output
out_path = "parsed/betfair_atp_tournament_summary.csv"
Path("parsed").mkdir(exist_ok=True)
grouped.to_csv(out_path, index=False)
print(f"✅ Saved ATP tournament summary to {out_path}")
