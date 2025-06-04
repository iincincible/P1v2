import pandas as pd
import argparse
from pathlib import Path
from rapidfuzz import fuzz

def normalize(name):
    return str(name).lower().replace(".", "").replace("-", " ").strip()

def resolve_player(betfair_name, roster_map, alias_map, use_fuzzy):
    if betfair_name in alias_map:
        return alias_map[betfair_name]

    clean_bf = normalize(betfair_name)

    # Direct containment
    for rc, full_name in roster_map.items():
        if rc in clean_bf or clean_bf in rc:
            return full_name

    # Fuzzy fallback
    if use_fuzzy:
        best_match = None
        best_score = 0
        for rc, full_name in roster_map.items():
            score = fuzz.token_sort_ratio(clean_bf, rc)
            if score > best_score:
                best_score = score
                best_match = full_name
        return best_match if best_score >= 80 else None

    return None

def build_matches(args):
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.dropna(subset=["runner_name", "ltp", "market_id", "selection_id", "timestamp"])
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64")
    snaps = snaps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    # Build 2-runner market map
    runner_map = {}
    for mid, group in snaps.groupby("market_id"):
        g = group.sort_values("selection_id")
        runners = list(g["runner_name"])
        odds = list(g["ltp"])
        if len(runners) == 2:
            runner_map[mid] = {"runners": runners, "odds": odds}

    if args.snapshot_only:
        clean_rows = [
            {
                "market_id": mid,
                "player_1": data["runners"][0],
                "player_2": data["runners"][1],
                "odds_player_1": data["odds"][0],
                "odds_player_2": data["odds"][1],
            }
            for mid, data in runner_map.items()
        ]
        df_out = pd.DataFrame(clean_rows)
        Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(args.output_csv, index=False)
        print(f"✅ Saved {len(df_out)} snapshot-only matches to {args.output_csv}")
        return

    # Load Sackmann results
    sack = pd.read_csv(args.sackmann_csv)
    sack["match_date"] = pd.to_datetime(sack["tourney_date"], format="%Y%m%d", errors="coerce").dt.date
    sack["winner_clean"] = sack["winner_name"].map(normalize)
    sack["loser_clean"] = sack["loser_name"].map(normalize)

    # Optional alias map
    alias_map = {}
    if args.alias_csv and Path(args.alias_csv).exists():
        alias_df = pd.read_csv(args.alias_csv)
        alias_map = dict(zip(alias_df["alias"].str.strip(), alias_df["full_name"].str.strip()))

    # Roster map for fuzzy matching
    roster = pd.Series(pd.concat([sack["winner_name"], sack["loser_name"]], ignore_index=True).unique())
    roster_clean = roster.map(normalize).tolist()
    roster_map = dict(zip(roster_clean, roster))

    # Optional tourney name filter
    if args.tournament:
        sack = sack[sack["tourney_name"].str.lower().str.contains(args.tournament.lower().replace("_", " "))]

    matched_rows = []

    for mid, data in runner_map.items():
        r1, r2 = data["runners"]
        m1 = resolve_player(r1, roster_map, alias_map, args.fuzzy_match)
        m2 = resolve_player(r2, roster_map, alias_map, args.fuzzy_match)

        if not m1 or not m2:
            continue

        match = sack[
            ((sack["winner_name"] == m1) & (sack["loser_name"] == m2)) |
            ((sack["winner_name"] == m2) & (sack["loser_name"] == m1))
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
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df_out)} matched results to {args.output_csv}")

# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tour", required=True)
    parser.add_argument("--tournament", required=False)
    parser.add_argument("--year", type=int, required=False)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--sackmann_csv", required=False)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--alias_csv", required=False)
    parser.add_argument("--fuzzy_match", action="store_true")
    parser.add_argument("--snapshot_only", action="store_true")
    args = parser.parse_args()

    build_matches(args)
