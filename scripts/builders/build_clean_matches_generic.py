import pandas as pd
import argparse
from pathlib import Path
import hashlib
import os
from scripts.utils.matching import (
    normalize_name,
    load_alias_map,
    build_roster_map,
    resolve_player
)
from scripts.utils.logger import log_info, log_success, log_warning, log_error

def build_matches(args):
    if os.path.exists(args.output_csv):
        log_info(f"Output already exists: {args.output_csv}")
        return

    log_info(f"Loading snapshots: {args.snapshots_csv}")
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.dropna(subset=["runner_name", "ltp", "market_id", "selection_id", "timestamp"])
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64")
    snaps = snaps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    runner_map = {}
    for mid, group in snaps.groupby("market_id"):
        g = group.sort_values("selection_id")
        runners, odds = list(g["runner_name"]), list(g["ltp"])
        if len(runners) == 2:
            runner_map[mid] = {"runners": runners, "odds": odds}

    sack, alias_map, roster_map = None, {}, {}
    sack_exists = args.sackmann_csv and Path(args.sackmann_csv).exists()

    if sack_exists:
        sack = pd.read_csv(args.sackmann_csv)
        if sack.empty:
            log_warning("Sackmann file is empty — falling back to snapshot-only mode.")
            args.snapshot_only = True
        else:
            sack["match_date"] = pd.to_datetime(sack["tourney_date"], format="%Y%m%d", errors="coerce").dt.date
            if args.alias_csv and Path(args.alias_csv).exists():
                alias_map = load_alias_map(args.alias_csv)
            roster_map = build_roster_map(sack)
            if args.tournament:
                sack = sack[sack["tourney_name"].str.lower().str.contains(args.tournament.lower().replace("_", " "))]
    else:
        log_warning("Sackmann CSV not provided — falling back to snapshot-only mode.")
        args.snapshot_only = True

    matched_rows = []
    for mid, data in runner_map.items():
        r1, r2 = data["runners"]
        row = {
            "market_id": mid,
            "player_1": r1,
            "player_2": r2,
            "odds_player_1": data["odds"][0],
            "odds_player_2": data["odds"][1],
            "match_id": hashlib.sha1(f"{r1}|{r2}|{mid}".encode()).hexdigest()[:10]
        }
        if not args.snapshot_only and sack is not None:
            m1 = resolve_player(r1, roster_map, alias_map, args.fuzzy_match)
            m2 = resolve_player(r2, roster_map, alias_map, args.fuzzy_match)
            if m1 and m2:
                match = sack[((sack["winner_name"] == m1) & (sack["loser_name"] == m2)) |
                             ((sack["winner_name"] == m2) & (sack["loser_name"] == m1))]
                if not match.empty:
                    sack_row = match.iloc[0]
                    row.update({
                        "actual_winner": sack_row["winner_name"],
                        "winner_name": sack_row["winner_name"],
                        "loser_name": sack_row["loser_name"],
                        "match_date": sack_row["match_date"]
                    })
        matched_rows.append(row)

    df_out = pd.DataFrame(matched_rows)

    if args.player_stats_csv and Path(args.player_stats_csv).exists():
        stats_df = pd.read_csv(args.player_stats_csv)
        join_col = args.join_stats_on
        df_out = df_out.merge(stats_df.add_suffix("_p1"), left_on="player_1", right_on=f"{join_col}_p1", how="left")
        df_out = df_out.merge(stats_df.add_suffix("_p2"), left_on="player_2", right_on=f"{join_col}_p2", how="left")
        log_info(f"Enriched with player stats: {args.player_stats_csv}")

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output_csv, index=False)
    log_success(f"Saved {len(df_out)} matches to {args.output_csv}")

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
    parser.add_argument("--player_stats_csv", required=False)
    parser.add_argument("--join_stats_on", default="player_name")
    args = parser.parse_args()
    build_matches(args)
