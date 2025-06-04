import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

# === Inputs ===
snap_path = "parsed/betfair_tennis_snapshots_iw2023_wta_filtered_strict.csv"
sack_path = "parsed/indianwells_2023_wta_matches.csv"
alias_path = "configs/player_aliases.csv"
output_path = "data/processed/indianwells_2023_wta_merged_snapshot_results.csv"

# === Load snapshots ===
snap = pd.read_csv(snap_path)
snap["market_id"] = snap["market_id"].astype(str)
snap["timestamp"] = pd.to_datetime(snap["timestamp"])
snap = snap.dropna(subset=["runner_name", "ltp"])
snap = snap.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

# === Build 2-runner markets
runner_map = {}
for mid, group in snap.groupby("market_id"):
    g = group.sort_values("selection_id")
    if len(g) == 2:
        runner_map[mid] = {
            "runners": list(g["runner_name"]),
            "odds": list(g["ltp"])
        }

# === Load Sackmann results
sack = pd.read_csv(sack_path)
sack["match_date"] = pd.to_datetime(sack["tourney_date"]).dt.date
sack["winner_clean"] = sack["winner_name"].str.lower().str.replace("[^a-z0-9 ]", "", regex=True)
sack["loser_clean"] = sack["loser_name"].str.lower().str.replace("[^a-z0-9 ]", "", regex=True)

# === Build player roster
roster = pd.Series(
    pd.concat([sack["winner_name"], sack["loser_name"]], ignore_index=True).unique()
)
roster_clean = roster.str.lower().str.replace("[^a-z0-9 ]", "", regex=True).tolist()
roster_map = dict(zip(roster_clean, roster))

# === Load alias map
alias_map = {}
if Path(alias_path).exists():
    alias_df = pd.read_csv(alias_path)
    alias_map = dict(zip(alias_df["alias"].str.strip(), alias_df["full_name"].str.strip()))

# === Normalization
def normalize(x):
    return str(x).lower().replace(".", "").replace("-", " ").strip()

# === Match to Sackmann name
def resolve_player(betfair_name):
    if betfair_name in alias_map:
        return alias_map[betfair_name]

    clean_bf = normalize(betfair_name)
    best_match = None
    best_score = 0

    for rc, full_name in roster_map.items():
        if rc in clean_bf or clean_bf in rc:
            return full_name
        score = fuzz.token_sort_ratio(clean_bf, rc)
        if score > best_score:
            best_score = score
            best_match = full_name

    return best_match if best_score >= 80 else None

# === Match snapshot runners to Sackmann results
matched_rows = []
for mid, data in runner_map.items():
    r1, r2 = data["runners"]
    m1 = resolve_player(r1)
    m2 = resolve_player(r2)

    if not m1 or not m2:
        continue

    match = sack[
        ((sack["winner_name"] == m1) & (sack["loser_name"] == m2)) |
        ((sack["winner_name"] == m2) & (sack["loser_name"] == m1))
    ]
    if match.empty:
        continue

    row = match.iloc[0]
    actual_winner = row["winner_name"]
    matched_rows.append({
        "market_id": mid,
        "player_1": r1,
        "player_2": r2,
        "odds_player_1": data["odds"][0],
        "odds_player_2": data["odds"][1],
        "actual_winner": actual_winner,
        "winner_name": row["winner_name"],
        "loser_name": row["loser_name"],
        "match_date": row["match_date"]
    })

# === Save output
df_out = pd.DataFrame(matched_rows)
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(output_path, index=False)
print(f"✅ Matched {len(df_out)} Indian Wells WTA matches to {output_path}")
