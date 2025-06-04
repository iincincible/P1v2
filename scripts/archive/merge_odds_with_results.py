import os
import pandas as pd
from datetime import datetime, timedelta
import argparse

def normalize(name):
    return name.strip().lower() if isinstance(name, str) else ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--odds_csv", required=True, help="Path to the historical odds CSV file")
    parser.add_argument("--match_csv", required=True, help="Path to the ATP/WTA match CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save the merged output CSV")
    args = parser.parse_args()

    odds_df = pd.read_csv(args.odds_csv)
    match_df = pd.read_csv(args.match_csv)

    odds_df["timestamp"] = pd.to_datetime(odds_df["timestamp"], errors="coerce")
    odds_df["snapshot_date"] = odds_df["timestamp"].dt.date
    match_df["match_date"] = pd.to_datetime(match_df["tourney_date"], format="%Y%m%d", errors="coerce").dt.date

    odds_df["p1_norm"] = odds_df["runner_1"].apply(normalize)
    odds_df["p2_norm"] = odds_df["runner_2"].apply(normalize)
    match_df["w_norm"] = match_df["winner_name"].apply(normalize)
    match_df["l_norm"] = match_df["loser_name"].apply(normalize)

    merged_rows = []

    for _, odds_row in odds_df.iterrows():
        for delta in [-1, 0, 1]:  # allow 1-day wiggle
            match_date = odds_row["snapshot_date"] + timedelta(days=delta)
            candidates = match_df[match_df["match_date"] == match_date]

            for _, match_row in candidates.iterrows():
                odds_players = {odds_row["p1_norm"], odds_row["p2_norm"]}
                match_players = {match_row["w_norm"], match_row["l_norm"]}

                if odds_players == match_players:
                    merged_rows.append({
                        "market_id": odds_row["market_id"],  # ✅ Added to enable LTP joins
                        "snapshot_date": odds_row["snapshot_date"],
                        "match_date": match_row["match_date"],
                        "winner": match_row["winner_name"],
                        "loser": match_row["loser_name"],
                        "player_1": odds_row["runner_1"],
                        "player_2": odds_row["runner_2"],
                        "odds_player_1": None,
                        "odds_player_2": None,
                        "implied_prob_1": None,
                        "implied_prob_2": None,
                        "bookmaker": None,
                        "actual_winner": match_row["winner_name"],
                        "p1_is_winner": odds_row["runner_1"] == match_row["winner_name"],
                        "p2_is_winner": odds_row["runner_2"] == match_row["winner_name"]
                    })
                    break

    merged_df = pd.DataFrame(merged_rows)
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    merged_df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(merged_df)} merged matches to {args.output_csv}")

if __name__ == "__main__":
    main()
