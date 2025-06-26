import pandas as pd

# File to patch
file = "data/processed/ausopen_2023_atp_predictions_withodds.csv"

df = pd.read_csv(file)

if "winner_name" in df.columns:
    df["actual_winner"] = df["winner_name"]
    df.to_csv(file, index=False)
    print("✅ Patched file: 'actual_winner' column added (copied from winner_name).")
else:
    print(
        "❌ No 'winner_name' column found! Cannot patch. Check your pipeline outputs."
    )
