import pandas as pd
import argparse
from pathlib import Path

def normalize(name):
    return str(name).lower().replace(".", "").replace("-", " ").strip()

def build_clean_matches(
    tour: str,
    tournament: str,
    year: int,
    snapshots_csv: str,
    sackmann_csv: str,
    output_csv: str
):
    # === Load snapshots ===
    snaps = pd.read_csv(snapshots_csv)
    snaps = snaps.dropna(subset=["runner_name", "ltp", "market_id", "selection_id", "timestamp"])
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64")
    snaps = snaps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    # === Build runner map for 2-runner markets ===
    runner_map = {}
    for mid, group in snaps.groupby("market_id"):
        g = group.sort_values("selection_id")
        runners = list(g["runner_name"])
        odds = list(g["ltp"])
        if len(runners) == 2:
            runner_map[mid] = {"runners": runners, "odds": odds}

    # === Load Sackmann results ===
    sack = pd.read_csv(sackmann_csv)
    sack["match_date"] = pd.to_datetime(sack["tourney_date"], format="%Y%m%d", errors="coerce").dt.date
    sack["winner_clean"] = sack["winner_name"].map(normalize)
    sack["loser_clean"] = sack["loser_name"].map(normalize)

    # Optional: restrict by tourney name
    tourney_filter = tournament.lower().replace("_", " ")
    sack = sack[sack["tourney_name"].str.lower().str.contains(tourney_filter)]

    matched_rows = []

    for mid, data in runner_map.items():
        r1, r2 = data["runners"]
        rc1, rc2 = normalize(r1), normalize(r2)

        matched = sack[
            ((sack["winner_clean"] == rc1) & (sack["loser_clean"] == rc2)) |
            ((sack["winner_clean"] == rc2) & (sack["loser_clean"] == rc1))
        ]

        if not matched.empty:
            m = matched.iloc[0]
            actual_winner = m["winner_name"]
            matched_rows.append({
                "market_id": mid,
                "player_1": r1,
                "player_2": r2,
                "odds_player_1": data["odds"][0],
                "odds_player_2": data["odds"][1],
                "actual_winner": actual_winner,
                "winner_name": m["winner_name"],
                "loser_name": m["loser_name"],
                "match_date": m["match_date"],
            })

    df_out = pd.DataFrame(matched_rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    print(f"✅ Saved {len(df_out)} matches to {output_csv}")

# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tour", required=True)
    parser.add_argument("--tournament", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--sackmann_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    build_clean_matches(
        tour=args.tour,
        tournament=args.tournament,
        year=args.year,
        snapshots_csv=args.snapshots_csv,
        sackmann_csv=args.sackmann_csv,
        output_csv=args.output_csv
    )
