import pandas as pd
import glob

files = glob.glob("data/processed/bankroll_sim_*_2023_deduped.csv")
for f in sorted(files):
    try:
        df = pd.read_csv(f, nrows=1)
        cols = df.columns.tolist()
        print(f"{f}: {'✅ OK' if all(c in cols for c in ['player_staked', 'stake', 'player_payout']) else '❌ Missing'} → {cols}")
    except Exception as e:
        print(f"{f}: ❌ Error reading file — {e}")