import argparse
import os
import bz2
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

def should_parse_file(file_path, start_date, end_date):
    try:
        parts = file_path.parts
        year, month, day = parts[-5], parts[-4], parts[-3]
        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d")
        return start_date <= dt <= end_date
    except Exception:
        return False

def parse_file(file_path, mode):
    records = []
    open_func = bz2.open if file_path.suffix == ".bz2" else open

    try:
        with open_func(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                if data.get("op") != "mcm":
                    continue

                for mc in data.get("mc", []):
                    market_id = mc.get("id", "")
                    market_def = mc.get("marketDefinition", {})
                    if not market_def or market_def.get("marketType") != "MATCH_ODDS":
                        continue

                    market_time = market_def.get("marketTime")
                    market_name = market_def.get("name", "")
                    runners = market_def.get("runners", [])

                    if len(runners) != 2:
                        continue

                    runner_1 = runners[0].get("name", "")
                    runner_2 = runners[1].get("name", "")
                    selection_id_1 = runners[0].get("id")
                    selection_id_2 = runners[1].get("id")

                    if mode == "metadata":
                        records.append({
                            "market_id": market_id,
                            "market_time": market_time,
                            "market_name": market_name,
                            "runner_1": runner_1,
                            "runner_2": runner_2
                        })
                        return records

                    if mode == "full":
                        records.append({
                            "market_id": market_id,
                            "selection_id": selection_id_1,
                            "ltp": None,
                            "timestamp": data.get("pt", None),
                            "market_time": market_time,
                            "market_name": market_name,
                            "runner_name": runner_1,
                            "runner_1": runner_1,
                            "runner_2": runner_2
                        })
                        records.append({
                            "market_id": market_id,
                            "selection_id": selection_id_2,
                            "ltp": None,
                            "timestamp": data.get("pt", None),
                            "market_time": market_time,
                            "market_name": market_name,
                            "runner_name": runner_2,
                            "runner_1": runner_1,
                            "runner_2": runner_2
                        })

                    for rc in mc.get("rc", []):
                        row = {
                            "market_id": market_id,
                            "selection_id": rc.get("id"),
                            "ltp": rc.get("ltp", None),
                            "timestamp": data.get("pt", None),
                            "market_time": market_time,
                            "market_name": market_name,
                            "runner_1": runner_1,
                            "runner_2": runner_2
                        }

                        if mode == "full":
                            row["runner_name"] = next((r.get("name") for r in runners if r.get("id") == rc.get("id")), None)

                        records.append(row)

                    if mode == "ltp_only":
                        break
    except Exception as e:
        print(f"❌ Failed: {file_path} — {e}")
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--mode", choices=["full", "ltp_only", "metadata"], default="full")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    root = Path(args.input_dir)
    all_files = [f for f in root.rglob("*.bz2") if should_parse_file(f, start, end)]

    print(f"🔍 Found {len(all_files)} files in range")

    all_records = []
    for file in tqdm(all_files, desc="Parsing files"):
        all_records.extend(parse_file(file, args.mode))

    if not all_records:
        print("⚠️ No records extracted.")
        return

    df = pd.DataFrame(all_records)
    if args.mode != "metadata":
        df = df.dropna(subset=["selection_id"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
    df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} rows to {args.output_csv}")

if __name__ == "__main__":
    main()
