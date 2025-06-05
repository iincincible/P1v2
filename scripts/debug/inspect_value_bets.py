import pandas as pd
import os
import glob

def main():
    files = glob.glob("data/processed/*_value_bets.csv")
    if not files:
        print("❌ No value bet files found.")
        return

    for f in files:
        print(f"\n📝 {f}")
        if os.path.getsize(f) == 0:
            print("⚠️ File is empty.")
            continue
        try:
            df = pd.read_csv(f)
            print(f"✅ Rows: {len(df)}")
            print(f"✅ Columns: {df.columns.tolist()}")
        except Exception as e:
            print(f"❌ Failed to read: {e}")

if __name__ == "__main__":
    main()
