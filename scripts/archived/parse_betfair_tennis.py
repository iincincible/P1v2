import os
import bz2
import json
import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from datetime import datetime

def should_parse_folder(folder_path, start_date, end_date):
    try:
        parts = folder_path.parts
        year, month, day = parts[-5], parts[-4], parts[-3]
        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d")
        return start_date <= dt <= end_date
    except Exception:
        return False

def extract_snapshots_from_file(file_path):
    data = []
    open_func = bz2.open if file_path.suffix == ".bz2" else open

    try:
        with open_func(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    if msg.get("op") != "mcm":
                        continue

                    for mc in msg.get("mc", []):
                        market_id = mc.get("id", "")
                        market_def = mc.get("marketDefinition", {})

                        if not market_def:
                            continue
                        if market_def.get("marketType") != "MATCH_ODDS":
                            continue
                        runners = market_def.get("runners", [])
                        if len(runners) != 2:
                            continue

                        market_time = market_def.get("marketTime")
                        market_name = market_def.get("name", "")

                        # Extract full names from runners array
                        runner_1 = runners[0].get("name", "")
                        runner_2 = runners[1].get("name", "")

                        for rc in mc.get("rc", []):
                            row = {
                                "market_id": market_id,
                                "selection_id": rc.get("id"),
                                "ltp": rc.get("ltp", None),
                                "timestamp": msg.get("pt", None),
                                "market_time": market_time,
                                "market_name": market_name,
                                "runner_1": runner_1,
                                "runner_2": runner_2
                            }
                            data.append(row)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"❌ Failed to process {file_path}: {e}")

    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True, help="Root folder containing Betfair BASIC data")
    parser.add_argument("--output_csv", default="parsed/betfair_tennis_snapshots.csv", help="Output CSV path")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    root = Path(args.input_dir)
    all_files = list(root.rglob("*"))
    tennis_files = [f for f in all_files if f.suffix in [".bz2", ""] and should_parse_folder(f, start, end)]

    print(f"🔍 Found {len(tennis_files)} tennis market files in range {args.start_date} to {args.end_date}")

    all_snapshots = []
    for file in tqdm(tennis_files, desc="Parsing tennis market files"):
        snapshots = extract_snapshots_from_file(file)
        all_snapshots.extend(snapshots)

    if all_snapshots:
        df = pd.DataFrame(all_snapshots)
        df = df.dropna(subset=["ltp"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
        df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")

        os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
        df.to_csv(args.output_csv, index=False)
        print(f"✅ Parsed {len(df)} snapshot rows to {args.output_csv}")
    else:
        print("⚠️ No snapshot data found.")

if __name__ == "__main__":
    main()
