import pandas as pd
import bz2
import json
import os
from tqdm import tqdm

# Input: filtered file list from scan
input_csv = "parsed/betfair_tennis_snapshots_ausopen2023.csv"

# Output: snapshot data
output_csv = "parsed/betfair_tennis_snapshots.csv"
snapshots = []

df_files = pd.read_csv(input_csv)
seen_files = set()

for _, row in tqdm(df_files.iterrows(), total=len(df_files)):
    path = row["filepath"]
    if path in seen_files:
        continue
    seen_files.add(path)

    try:
        with bz2.open(path, "rt") as f:
            for line in f:
                data = json.loads(line)
                if data.get("op") != "mcm":
                    continue
                for mc in data.get("mc", []):
                    market_id = mc.get("id", "")
                    market_def = mc.get("marketDefinition", {})
                    market_time = market_def.get("marketTime")
                    market_name = market_def.get("name", "")
                    runners = market_def.get("runners", [])

                    for runner in runners:
                        snapshots.append({
                            "market_id": market_id,
                            "selection_id": runner.get("id"),
                            "runner_name": runner.get("name", ""),
                            "market_name": market_name,
                            "market_time": market_time,
                        })
                    break  # Only first mc with runners
                break  # Only need initial snapshot with metadata
    except Exception:
        continue

pd.DataFrame(snapshots).to_csv(output_csv, index=False)
print(f"\n✅ Extracted {len(snapshots)} snapshot rows to {output_csv}")
