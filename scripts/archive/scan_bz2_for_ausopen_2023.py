import os
import bz2
import json
import pandas as pd
from tqdm import tqdm

# Adjust this to your Betfair BASIC directory root
ROOT = "data/BASIC/2023/Jan"

# We'll collect snapshots that mention AusOpen ATP players
ATP_PLAYERS = [
    "daniil medvedev", "jannik sinner", "john millman",
    "stefanos tsitsipas", "marton fucsovics", "sebastian korda",
    "lloyd harris", "taro daniel", "rinky hijikata", "stan wawrinka"
]

# Output CSV
output_csv = "parsed/betfair_tennis_snapshots_ausopen2023.csv"
results = []

def extract_from_bz2(filepath):
    try:
        with bz2.open(filepath, "rt") as f:
            for line in f:
                data = json.loads(line)
                if data.get("op") == "mcm":
                    for mc in data.get("mc", []):
                        market_def = mc.get("marketDefinition", {})
                        market_name = market_def.get("name", "")
                        runners = market_def.get("runners", [])
                        market_id = market_def.get("id", "")
                        for runner in runners:
                            runner_name = runner.get("name", "").lower()
                            if any(p in runner_name for p in ATP_PLAYERS):
                                results.append({
                                    "market_id": market_id,
                                    "market_name": market_name,
                                    "runner": runner.get("name", ""),
                                    "filepath": filepath
                                })
                                return  # Only need one match per file
    except Exception as e:
        pass  # Skip corrupt or unreadable files

# Recursively scan .bz2 files
for root, _, files in os.walk(ROOT):
    for fname in files:
        if fname.endswith(".bz2"):
            extract_from_bz2(os.path.join(root, fname))

# Save matched snapshot paths
df = pd.DataFrame(results)
df.to_csv(output_csv, index=False)
print(f"✅ Saved {len(df)} rows to {output_csv}")
