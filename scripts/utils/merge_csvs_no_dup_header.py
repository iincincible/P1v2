import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=True, help="Glob pattern for input CSVs")
    parser.add_argument("--output_csv", required=True, help="Path to output merged CSV")
    args = parser.parse_args()

    # Match files
    from glob import glob
    files = glob(args.input_glob)
    if not files:
        raise FileNotFoundError(f"No files found for glob: {args.input_glob}")
    print(f"📄 Found {len(files)} files")

    all_dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            df["source_file"] = Path(file).name
            all_dfs.append(df)
        except Exception as e:
            print(f"⚠️ Skipped {file}: {e}")

    if not all_dfs:
        raise ValueError("❌ No CSVs could be loaded")

    merged_df = pd.concat(all_dfs, ignore_index=True)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved merged CSV to {args.output_csv} with {len(merged_df)} rows")

if __name__ == "__main__":
    main()
