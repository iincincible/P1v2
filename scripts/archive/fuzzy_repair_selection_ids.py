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

print(f"✨ Loading {args.merged_csv} and {args.snapshots_csv}")
match_df = pd.read_csv(args.merged_csv)
snap_df = pd.read_csv(args.snapshots_csv)

# Clean and prepare
match_df["market_id"] = match_df["market_id"].astype(str)
snap_df["market_id"] = snap_df["market_id"].astype(str)
snap_df["runner_clean"] = snap_df["runner_name"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
snap_df = snap_df.dropna(subset=["runner_clean", "selection_id"])

# Build fuzzy matching lookup by market
runner_map = (
    snap_df.groupby("market_id")
    .apply(lambda g: list(zip(g["runner_clean"], g["selection_id"])))
    .to_dict()
)

selection_id_1, selection_id_2 = [], []
tqdm.pandas(desc="🔍 Advanced Fuzzy Matching")

for _, row in tqdm(match_df.iterrows(), total=len(match_df)):
    mid = str(row["market_id"])
    p1 = str(row["player_1"]).lower()
    p2 = str(row["player_2"]).lower()

    sid1 = sid2 = None
    candidates = runner_map.get(mid, [])
    for rc, sid in candidates:
        if sid1 is None and fuzz.token_set_ratio(p1, rc) >= args.threshold:
            sid1 = sid
        elif sid2 is None and fuzz.token_set_ratio(p2, rc) >= args.threshold:
            sid2 = sid

    selection_id_1.append(sid1)
    selection_id_2.append(sid2)

match_df["selection_id_1"] = selection_id_1
match_df["selection_id_2"] = selection_id_2

match_df.to_csv(args.output_csv, index=False)
print(f"✅ Saved repaired file to {args.output_csv}")
print("🔎 Match counts:")
print(match_df[["selection_id_1", "selection_id_2"]].notna().sum())
