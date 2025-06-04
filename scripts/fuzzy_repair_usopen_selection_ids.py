
import pandas as pd
from thefuzz import fuzz
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--merged_csv", required=True)
parser.add_argument("--snapshots_csv", required=True)
parser.add_argument("--output_csv", required=True)
parser.add_argument("--threshold", type=int, default=85)
args = parser.parse_args()

# === Load files ===
match_df = pd.read_csv(args.merged_csv)
snap_df = pd.read_csv(args.snapshots_csv)

match_df["market_id"] = match_df["market_id"].astype(str)
snap_df["market_id"] = snap_df["market_id"].astype(str)

# === Build snapshot lookup ===
snap_df["runner_clean"] = snap_df["runner_name"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
snap_df = snap_df.dropna(subset=["runner_clean", "selection_id"])
snap_lookup = snap_df.groupby("market_id")[["runner_clean", "selection_id"]].agg(list).to_dict()

# === Fuzzy match selection_ids ===
selection_id_1, selection_id_2 = [], []
tqdm.pandas(desc="🔍 Matching")

for idx, row in tqdm(match_df.iterrows(), total=len(match_df)):
    m_id = str(row["market_id"])
    p1 = str(row["player_1"]).lower()
    p2 = str(row["player_2"]).lower()

    snap_runners = snap_lookup.get("runner_clean", {}).get(m_id, [])
    snap_ids = snap_lookup.get("selection_id", {}).get(m_id, [])

    id1 = id2 = None
    for runner, sel_id in zip(snap_runners, snap_ids):
        score1 = fuzz.ratio(p1, runner)
        score2 = fuzz.ratio(p2, runner)
        if score1 >= args.threshold and id1 is None:
            id1 = sel_id
        elif score2 >= args.threshold and id2 is None:
            id2 = sel_id

    selection_id_1.append(id1)
    selection_id_2.append(id2)

match_df["selection_id_1"] = selection_id_1
match_df["selection_id_2"] = selection_id_2
match_df.to_csv(args.output_csv, index=False)
print(f"✅ Saved repaired file to {args.output_csv}")
