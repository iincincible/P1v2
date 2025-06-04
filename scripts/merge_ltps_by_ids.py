import pandas as pd
from thefuzz import fuzz
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--merged_csv", required=True)
parser.add_argument("--ltps_csv", required=True)
parser.add_argument("--output_csv", required=True)
args = parser.parse_args()

# Load data
merged = pd.read_csv(args.merged_csv)
snapshots = pd.read_csv(args.ltps_csv)

# Prep types
merged["market_id"] = merged["market_id"].astype(str)
snapshots["market_id"] = snapshots["market_id"].astype(str)

merged["selection_id_1"] = pd.to_numeric(merged["selection_id_1"], errors="coerce").astype("Int64")
merged["selection_id_2"] = pd.to_numeric(merged["selection_id_2"], errors="coerce").astype("Int64")
snapshots["selection_id"] = pd.to_numeric(snapshots["selection_id"], errors="coerce").astype("Int64")

# Exact LTP merge by selection_id
merged["ltp_player_1"] = merged.merge(
    snapshots[["market_id", "selection_id", "ltp"]],
    left_on=["market_id", "selection_id_1"],
    right_on=["market_id", "selection_id"],
    how="left"
)["ltp"]

merged["ltp_player_2"] = merged.merge(
    snapshots[["market_id", "selection_id", "ltp"]],
    left_on=["market_id", "selection_id_2"],
    right_on=["market_id", "selection_id"],
    how="left"
)["ltp"]

# Fuzzy fallback if LTP is missing
def fuzzy_lookup(row, player_col, fallback_col):
    if pd.notna(row[fallback_col]):
        return row[fallback_col]
    snap = snapshots[snapshots["market_id"] == row["market_id"]]
    best_score = -1
    best_ltp = None
    for _, srow in snap.iterrows():
        score = fuzz.token_set_ratio(str(row[player_col]).lower(), str(srow["runner_name"]).lower())
        if score > 90 and score > best_score:
            best_score = score
            best_ltp = srow["ltp"]
    return best_ltp

tqdm.pandas(desc="🔍 Fuzzy fallback for player 1")
merged["ltp_player_1"] = merged.progress_apply(lambda r: fuzzy_lookup(r, "player_1", "ltp_player_1"), axis=1)

tqdm.pandas(desc="🔍 Fuzzy fallback for player 2")
merged["ltp_player_2"] = merged.progress_apply(lambda r: fuzzy_lookup(r, "player_2", "ltp_player_2"), axis=1)

# Save
merged.to_csv(args.output_csv, index=False)
total = len(merged)
matched = merged["ltp_player_1"].notna().sum() + merged["ltp_player_2"].notna().sum()
print(f"✅ Merged LTPs for approx {matched // 2} / {total} matches")
print(f"📁 Saved patched output to {args.output_csv}")
