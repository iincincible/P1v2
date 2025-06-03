import argparse
import glob
import pandas as pd
from tqdm import tqdm
from pathlib import Path

def add_won_column(df):
    if 'winner_name' not in df.columns or 'player_1' not in df.columns:
        raise ValueError("Missing required columns: 'winner_name' or 'player_1'.")

    # Create 'won' as 1 if player_1 == winner_name else 0
    df['won'] = (df['player_1'] == df['winner_name']).astype(int)
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=True, help="Glob pattern for input CSV files")
    args = parser.parse_args()

    files = glob.glob(args.input_glob)
    for file in tqdm(files, desc="Patching 'won' column"):
        try:
            df = pd.read_csv(file)
            df = add_won_column(df)
            df.to_csv(file, index=False)
        except Exception as e:
            print(f"❌ Error in {file}: {e}")

if __name__ == "__main__":
    main()
