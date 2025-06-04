import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

# === Inputs ===
snap_path = "data/processed/indianwells_2023_atp_clean_snapshot_matches.csv"
sackmann_path = "parsed/indianwells_2023_atp_matches.csv"
output_path = "data/processed/indianwells_2023_atp_merged_snapshot_results.csv"

# === Load files ===
snap = pd.read_csv(snap_path)
sack = pd.read_csv(sackmann_path)
sack["match_date"] = pd.to_datetime(sack["tourney_date"], errors="coerce").dt.date

# === Normalize names ===
def norm(x):
    return str(x).lower().replace(".", "").replace("-", " ").strip()

snap["player_1_clean"] = snap["player_1"].map(norm)
snap["player_2_clean"] = snap["player_2"].map(norm)
snap["match_date"] = pd.NaT  # to be filled
snap["actual_winner"] = None
snap["winner_name"] = None
snap["loser_name"] = None

matched_rows = []

for _, snap_row in snap.iterrows():
    p1 = snap_row["player_1_clean"]
    p2 = snap_row["player_2_clean"]
    candidates = sack.copy()

    for _, cand in candidates.iterrows():
        w = norm(cand["winner_name"])
        l = norm(cand["loser_name"])
        if {p1, p2} == {w, l}:
            matched = {
                **snap_row.drop(labels=["player_1_clean", "player_2_clean"]).to_dict(),
                "match_date": cand["match_date"],
                "winner_name": cand["winner_name"],
                "loser_name": cand["loser_name"],
                "actual_winner": cand["winner_name"],
            }
            matched_rows.append(matched)
            break  # Stop after first match

# === Save output ===
df_out = pd.DataFrame(matched_rows)
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(output_path, index=False)
print(f"✅ Matched {len(df_out)} snapshot matches with Sackmann results")
print(f"📁 Saved to {output_path}")
