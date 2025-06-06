import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

# === Load snapshot data ===
snap = pd.read_csv("parsed/betfair_tennis_snapshots_iw2023_wta_filtered_strict.csv")
snap["timestamp"] = pd.to_datetime(snap["timestamp"])
snap = snap.sort_values("timestamp")
snap = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# === Extract valid 2-runner markets ===
runner_map = {}
for mid, group in snap.groupby("market_id"):
    sorted_group = group.sort_values("selection_id")
    runners = list(sorted_group["runner_name"])
    if len(runners) == 2:
        runner_map[mid] = {"runners": runners}

# === Load Sackmann results ===
sack = pd.read_csv("parsed/indianwells_2023_wta_matches.csv")
sack["tourney_date"] = pd.to_datetime(sack["tourney_date"])
sack["winner_clean"] = sack["winner_name"].str.lower().str.replace("[^a-z0-9 ]", "", regex=True)
sack["loser_clean"] = sack["loser_name"].str.lower().str.replace("[^a-z0-9 ]", "", regex=True)

def normalize(name):
    return str(name).lower().replace(".", "").replace("-", " ").strip()

# === Match and print unmatched runner pairs ===
unmatched = []
for mid, data in runner_map.items():
    r1, r2 = data["runners"]
    rc1, rc2 = normalize(r1), normalize(r2)

    found = False
    for _, row in sack.iterrows():
        wc, lc = row["winner_clean"], row["loser_clean"]
        if {rc1, rc2} == {wc, lc}:
            found = True
            break
        if fuzz.token_sort_ratio(rc1, wc) >= 85 and fuzz.token_sort_ratio(rc2, lc) >= 85:
            found = True
            break
        if fuzz.token_sort_ratio(rc1, lc) >= 85 and fuzz.token_sort_ratio(rc2, wc) >= 85:
            found = True
            break
    if not found:
        unmatched.append((r1, r2))

# === Output
print(f"❌ Unmatched runner pairs: {len(unmatched)}")
for r1, r2 in unmatched[:20]:
    print(f" - {r1} vs {r2}")
