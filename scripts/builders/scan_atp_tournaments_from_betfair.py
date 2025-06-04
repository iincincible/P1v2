import argparse
import os
import bz2
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def should_parse_file(file_path, start_date, end_date):
    try:
        year, month, day = file_path.parts[-5], file_path.parts[-4], file_path.parts[-3]
        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d")
        return start_date <= dt <= end_date
    except:
        return False

def extract_metadata(file_path):
    rows = []
    try:
        with bz2.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                if data.get("op") != "mcm":
                    continue
                for mc in data.get("mc", []):
                    market_def = mc.get("marketDefinition", {})
                    if market_def.get("marketType") != "MATCH_ODDS":
                        continue
                    runners = market_def.get("runners", [])
                    if len(runners) != 2:
                        continue
                    row = {
                        "market_id": mc.get("id", ""),
                        "market_time": market_def.get("marketTime"),
                        "market_name": market_def.get("name", ""),
                        "runner_1": runners[0].get("name", ""),
                        "runner_2": runners[1].get("name", ""),
                        "source_file": str(file_path)
                    }
                    rows.append(row)
    except Exception as e:
        print(f"❌ Failed to parse {file_path}: {e}")
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    files = [f for f in Path(args.input_dir).rglob("*.bz2") if should_parse_file(f, start, end)]
    print(f"🔍 Found {len(files):,} .bz2 files in range")

    all_rows = []
    for f in tqdm(files, desc="Scanning metadata"):
        all_rows.extend(extract_metadata(f))

    if not all_rows:
        print("⚠️ No markets found.")
        return

    df = pd.DataFrame(all_rows)
    df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")
    df = df.dropna(subset=["runner_1", "runner_2", "market_id"])

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} ATP candidate markets to {args.output_csv}")

if __name__ == "__main__":
    main()
