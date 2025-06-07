import pandas as pd
from pathlib import Path
import argparse
from scripts.utils.matching import (
    normalize_name,
    load_alias_map,
    build_roster_map,
    resolve_player
)

def match_snapshot_with_results(snapshot_csv, results_csv, output_csv, alias_csv=None, fuzzy=False):
    snap = pd.read_csv(snapshot_csv)
    results = pd.read_csv(results_csv)

    snap["timestamp"] = pd.to_datetime(snap["timestamp"])
    snap = snap.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    results["match_date"] = pd.to_datetime(results["tourney_date"], errors="coerce").dt.date
    results["winner_clean"] = results["winner_name"].map(normalize_name)
    results["loser_clean"] = results["loser_name"].map(normalize_name)

    alias_map = load_alias_map(alias_csv)
    roster_map = build_roster_map(results)

    runner_map = {}
    for mid, group in snap.groupby("market_id"):
        g = group.sort_values("selection_id")
        if len(g) == 2:
            runner_map[mid] = {
                "runners": list(g["runner_name"]),
                "odds": list(g["ltp"])
            }

    matched_rows = []
    for mid, data in runner_map.items():
        r1, r2 = data["runners"]
        m1 = resolve_player(r1, roster_map, alias_map, fuzzy)
        m2 = resolve_player(r2, roster_map, alias_map, fuzzy)

        if not m1 or not m2:
            continue

        match = results[
            ((results["winner_name"] == m1) & (results["loser_name"] == m2)) |
            ((results["winner_name"] == m2) & (results["loser_name"] == m1))
        ]
        if match.empty:
            continue

        row = match.iloc[0]
        matched_rows.append({
            "market_id": mid,
            "player_1": r1,
            "player_2": r2,
            "odds_player_1": data["odds"][0],
            "odds_player_2": data["odds"][1],
            "actual_winner": row["winner_name"],
            "winner_name": row["winner_name"],
            "loser_name": row["loser_name"],
            "match_date": row["match_date"]
        })

    df_out = pd.DataFrame(matched_rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    print(f"✅ Matched {len(df_out)} snapshot matches to results at {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot_csv", required=True)
    parser.add_argument("--results_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--alias_csv", required=False)
    parser.add_argument("--fuzzy", action="store_true")
    args = parser.parse_args()

    match_snapshot_with_results(
        snapshot_csv=args.snapshot_csv,
        results_csv=args.results_csv,
        output_csv=args.output_csv,
        alias_csv=args.alias_csv,
        fuzzy=args.fuzzy
    )
