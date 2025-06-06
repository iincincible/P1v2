import pandas as pd
from pathlib import Path
from collections import Counter
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--snapshots_csv", required=True)
parser.add_argument("--match_csv", required=True)
args = parser.parse_args()

# === Load snapshots ===
snap = pd.read_csv(args.snapshots_csv)
snap["timestamp"] = pd.to_datetime(snap["timestamp"])
snap = snap.dropna(subset=["runner_name", "ltp"])
snap = snap.sort_values("timestamp")

# === Build final snapshot per runner
finals = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# === Group into markets
market_counts = finals.groupby("market_id")["runner_name"].nunique()
usable_markets = market_counts[market_counts == 2].index

# === Load match file
matches = pd.read_csv(args.match_csv)
matches["match_date"] = pd.to_datetime(matches["tourney_date"])
all_players = pd.concat([matches["winner_name"], matches["loser_name"]]).dropna().unique()

# === Normalize
def normalize(x):
    return str(x).lower().replace(".", "").replace("-", " ").strip()

all_players_clean = set(map(normalize, all_players))
finals["runner_clean"] = finals["runner_name"].map(normalize)

# === Coverage diagnostic
matched_runners = finals[finals["runner_clean"].isin(all_players_clean)]
matched_market_ids = matched_runners["market_id"].value_counts()
matched_two_runner_markets = matched_market_ids[matched_market_ids == 2].index

print(f"📊 Snapshot file contains {len(finals)} runners in {len(market_counts)} unique markets.")
print(f"✅ {len(matched_two_runner_markets)} 2-runner markets matched Sackmann player names.")
print(f"❌ {len(market_counts) - len(matched_two_runner_markets)} markets missing or unmatched.")

# Optional: print some unmatched examples
unmatched = set(finals["runner_clean"].unique()) - all_players_clean
print("\n🧩 Sample unmatched runner names:")
for name in list(unmatched)[:15]:
    print(f" - {name}")
