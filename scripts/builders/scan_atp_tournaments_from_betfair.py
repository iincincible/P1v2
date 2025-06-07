import argparse
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from scripts.utils.snapshot_parser import SnapshotParser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    all_files = list(Path(args.input_dir).rglob("*.bz2"))
    parser_obj = SnapshotParser(mode="metadata")

    filtered = [f for f in all_files if parser_obj.should_parse_file(f, start, end)]
    print(f"🔍 Found {len(filtered)} .bz2 files in range")

    all_rows = []
    for f in tqdm(filtered, desc="Extracting metadata"):
        all_rows.extend(parser_obj.parse_file(f))

    if not all_rows:
        print("⚠️ No metadata rows found.")
        return

    df = pd.DataFrame(all_rows)
    df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")
    df = df.dropna(subset=["runner_1", "runner_2", "market_id"])

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} ATP candidate markets to {args.output_csv}")

if __name__ == "__main__":
    main()
