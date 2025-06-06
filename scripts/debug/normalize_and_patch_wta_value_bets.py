import pandas as pd
import glob
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns

def try_patch(df, path):
    try:
        df = normalize_columns(df)

        if "winner" not in df.columns:
            if "actual_winner" in df.columns and "player_1" in df.columns:
                df["winner"] = (
                    df["actual_winner"].str.strip().str.lower() ==
                    df["player_1"].str.strip().str.lower()
                ).astype(int)
                print(f"🩹 Patched 'winner' from actual_winner for: {os.path.basename(path)}")
            else:
                raise ValueError("Cannot compute 'winner' — missing actual_winner or player_1")

        df.to_csv(path, index=False)
        print(f"✅ Saved normalized + patched: {path}")
    except Exception as e:
        print(f"❌ Failed: {path} — {e}")

# Target WTA value bet files
files = glob.glob("data/processed/*_wta_value_bets.csv")
for f in files:
    try:
        df = pd.read_csv(f)
        try_patch(df, f)
    except Exception as e:
        print(f"❌ Could not load {f}: {e}")
