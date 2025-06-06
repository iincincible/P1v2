import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns

path = "data/processed/usopen_2023_atp_value_bets.csv"
df = pd.read_csv(path)

try:
    df = normalize_columns(df)

    if "winner" not in df.columns:
        if "won" in df.columns:
            df["winner"] = df["won"].astype(int)
            print("🩹 Patched 'winner' from 'won' column")
        else:
            raise ValueError("No 'won' column available to derive winner")

    df.to_csv(path, index=False)
    print(f"✅ Saved patched file to {path}")

except Exception as e:
    print(f"❌ Failed to patch: {e}")
