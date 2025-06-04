import argparse
import pandas as pd
import glob
from collections import defaultdict

def log_player_roi(input_glob, output_csv):
    files = glob.glob(input_glob)
    df_list = [pd.read_csv(f) for f in files]
    df = pd.concat(df_list, ignore_index=True)

    player_stats = defaultdict(lambda: {"bets": 0, "wins": 0, "stake": 0.0, "profit": 0.0, "ev_total": 0.0})

    for _, row in df.iterrows():
        player = row["player_staked"]
        player_stats[player]["bets"] += 1
        player_stats[player]["wins"] += int(row.get("win", 0))
        player_stats[player]["stake"] += row.get("stake", 0.0)
        player_stats[player]["profit"] += row.get("profit", row.get("player_payout", 0.0)) - row.get("stake", 0.0)
        player_stats[player]["ev_total"] += row.get("ev", 0.0)

    out_rows = []
    for player, stats in player_stats.items():
        bets = stats["bets"]
        stake = stats["stake"]
        roi = (stats["profit"] / stake * 100) if stake > 0 else 0
        winrate = stats["wins"] / bets if bets > 0 else 0
        avg_ev = stats["ev_total"] / bets if bets > 0 else 0

        out_rows.append({
            "player": player,
            "bets": bets,
            "wins": stats["wins"],
            "winrate": round(winrate, 4),
            "total_staked": round(stake, 2),
            "profit": round(stats["profit"], 2),
            "roi": round(roi, 2),
            "avg_ev": round(avg_ev, 4)
        })

    pd.DataFrame(out_rows).sort_values("roi", ascending=False).to_csv(output_csv, index=False)
    print(f"✅ Logged ROI by player to {output_csv}")


def log_matchup_roi(input_glob, output_csv):
    files = glob.glob(input_glob)
    df_list = [pd.read_csv(f) for f in files]
    df = pd.concat(df_list, ignore_index=True)

    matchup_stats = defaultdict(lambda: {"bets": 0, "wins": 0, "stake": 0.0, "profit": 0.0})

    for _, row in df.iterrows():
        # Try to infer side from match and player_staked
        side = "unknown"
        if "match" in row and pd.notna(row["match"]):
            parts = row["match"].split(" vs ")
            if len(parts) == 2:
                if row["player_staked"] == parts[0]:
                    side = "p1"
                elif row["player_staked"] == parts[1]:
                    side = "p2"

        matchup_key = f"{row.get('match', 'unknown')} ({side})"

        matchup_stats[matchup_key]["bets"] += 1
        matchup_stats[matchup_key]["wins"] += int(row.get("win", 0))
        matchup_stats[matchup_key]["stake"] += row.get("stake", 0.0)
        matchup_stats[matchup_key]["profit"] += row.get("profit", row.get("player_payout", 0.0)) - row.get("stake", 0.0)

    out_rows = []
    for matchup, stats in matchup_stats.items():
        bets = stats["bets"]
        stake = stats["stake"]
        roi = (stats["profit"] / stake * 100) if stake > 0 else 0
        winrate = stats["wins"] / bets if bets > 0 else 0

        out_rows.append({
            "matchup+side": matchup,
            "bets": bets,
            "wins": stats["wins"],
            "winrate": round(winrate, 4),
            "total_staked": round(stake, 2),
            "profit": round(stats["profit"], 2),
            "roi": round(roi, 2)
        })

    pd.DataFrame(out_rows).sort_values("roi", ascending=False).to_csv(output_csv, index=False)
    print(f"✅ Logged ROI by matchup+side to {output_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=True)
    parser.add_argument("--player_output_csv", required=True)
    parser.add_argument("--matchup_output_csv", required=True)
    args = parser.parse_args()

    log_player_roi(args.input_glob, args.player_output_csv)
    log_matchup_roi(args.input_glob, args.matchup_output_csv)


if __name__ == "__main__":
    main()
