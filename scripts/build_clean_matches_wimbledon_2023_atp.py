import pandas as pd
from datetime import datetime

# === Inputs ===
snap_path = "parsed/betfair_tennis_snapshots.csv"
match_path = "data/tennis_atp/atp_matches_2023.csv"
output_path = "data/processed/wimbledon_2023_atp_clean_snapshot_matches.csv"

# === Load match data (Wimbledon 2023) ===
matches = pd.read_csv(match_path, low_memory=False)
matches["tourney_date"] = pd.to_datetime(matches["tourney_date"], format="%Y%m%d")
matches = matches[
    (matches["tourney_date"] >= "2023-07-01") & (matches["tourney_date"] <= "2023-07-16")
].copy()
matches["match_date"] = matches["tourney_date"].dt.date

# === Load raw snapshots (don't drop duplicates yet) ===
snap = pd.read_csv(snap_path, usecols=["market_id", "selection_id", "ltp", "timestamp", "runner_name"])
snap["timestamp"] = pd.to_datetime(snap["timestamp"], errors="coerce")
snap["runner_clean"] = snap["runner_name"].str.lower().str.replace("-", " ").str.replace(".", "").str.strip()

# === Clean player names ===
matches["player_1_clean"] = matches["winner_name"].str.lower().str.replace("-", " ").str.replace(".", "").str.strip()
matches["player_2_clean"] = matches["loser_name"].str.lower().str.replace("-", " ").str.replace(".", "").str.strip()
matches["match_date"] = matches["tourney_date"].dt.date

# === Get latest LTP per market_id + selection_id ===
snap = snap.sort_values("timestamp")
snap = snap.dropna(subset=["ltp"])
latest_ltp = snap.drop_duplicates(["market_id", "selection_id"], keep="last")

# === Group markets that have exactly 2 runners ===
market_counts = latest_ltp.groupby("market_id")["selection_id"].nunique()
valid_market_ids = market_counts[market_counts == 2].index
latest_ltp = latest_ltp[latest_ltp["market_id"].isin(valid_market_ids)].copy()

# === Try to match match rows to valid markets ===
results = []
for _, match in matches.iterrows():
    for market_id, group in latest_ltp.groupby("market_id"):
        if len(group) != 2:
            continue
        r1, r2 = group.iloc[0], group.iloc[1]
        runners = {r1["runner_clean"], r2["runner_clean"]}
        players = {match["player_1_clean"], match["player_2_clean"]}

        if runners == players:
            out = match.to_dict()
            out["market_id"] = market_id
            out["market_time"] = max(r1["timestamp"], r2["timestamp"])

            # Assign correct odds to player_1 and player_2
            if r1["runner_clean"] == match["player_1_clean"]:
                out["odds_player_1"] = r1["ltp"]
                out["odds_player_2"] = r2["ltp"]
            else:
                out["odds_player_1"] = r2["ltp"]
                out["odds_player_2"] = r1["ltp"]

            out["player_1"] = match["winner_name"]
            out["player_2"] = match["loser_name"]
            out["actual_winner"] = match["winner_name"]
            results.append(out)
            break  # stop searching once a match is found

df = pd.DataFrame(results)
df.to_csv(output_path, index=False)
print(f"✅ Saved {len(df)} Wimbledon ATP matches to {output_path}")
