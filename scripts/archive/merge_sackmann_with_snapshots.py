import pandas as pd
import argparse

def merge_matches_with_ltps(match_csv, snapshots_csv, ltps_csv, output_csv):
    matches = pd.read_csv(match_csv)
    snaps = pd.read_csv(snapshots_csv)
    ltps = pd.read_csv(ltps_csv)

    # Fix date parsing
    matches["tourney_date"] = pd.to_datetime(matches["tourney_date"], errors="coerce")
    matches["match_date"] = matches["tourney_date"].dt.date

    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"], errors="coerce")
    snaps["snapshot_date"] = snaps["timestamp"].dt.date

    # Extract market-level runner names
    markets = snaps[["market_id", "market_time", "market_name", "runner_1", "runner_2"]].drop_duplicates("market_id")
    markets["match_date"] = pd.to_datetime(markets["market_time"], errors="coerce").dt.date

    # Loose merge by match date only
    merged = matches.merge(markets, on="match_date", how="inner")

    # Set player_1 as winner for consistent modeling
    merged["player_1"] = merged["winner_name"]
    merged["player_2"] = merged["loser_name"]
    merged["actual_winner"] = merged["winner_name"]

    # Do not join selection IDs or odds yet — leave for fuzzy repair
    merged.to_csv(output_csv, index=False)
    print(f"✅ Merged {len(merged)} loose match rows to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    merge_matches_with_ltps(args.match_csv, args.snapshots_csv, args.ltps_csv, args.output_csv)
