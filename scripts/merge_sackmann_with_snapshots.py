import pandas as pd
import argparse

def merge_matches_with_ltps(match_csv, snapshots_csv, ltps_csv, output_csv):
    matches = pd.read_csv(match_csv)
    snaps = pd.read_csv(snapshots_csv)
    ltps = pd.read_csv(ltps_csv)

    # Format match dates
    matches["tourney_date"] = pd.to_datetime(matches["tourney_date"], format="%Y%m%d")
    matches["match_date"] = matches["tourney_date"].dt.date

    # Parse snapshot timestamps
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps["snapshot_date"] = snaps["timestamp"].dt.date

    # Extract market-level runner names
    markets = snaps[["market_id", "market_time", "market_name", "runner_1", "runner_2"]].drop_duplicates("market_id")
    markets["match_date"] = pd.to_datetime(markets["market_time"]).dt.date

    # Merge by match_date (loose first pass)
    merged = matches.merge(
        markets,
        on="match_date",
        how="inner"
    )

    # Filter to exact name matches between Sackmann and runners
    merged = merged[
        (merged["winner_name"].isin(merged["runner_1"]) | merged["winner_name"].isin(merged["runner_2"])) &
        (merged["loser_name"].isin(merged["runner_1"]) | merged["loser_name"].isin(merged["runner_2"]))
    ]

    # ✅ Set player_1 as winner for class balance
    merged["player_1"] = merged["winner_name"]
    merged["player_2"] = merged["loser_name"]
    merged["actual_winner"] = merged["winner_name"]

    # Merge selection IDs per player
    r1_map = snaps[["market_id", "runner_1", "selection_id"]].drop_duplicates()
    r1_map = r1_map.rename(columns={"runner_1": "player_1", "selection_id": "selection_id_1"})

    r2_map = snaps[["market_id", "runner_2", "selection_id"]].drop_duplicates()
    r2_map = r2_map.rename(columns={"runner_2": "player_2", "selection_id": "selection_id_2"})

    merged = merged.merge(r1_map, on=["market_id", "player_1"], how="left")
    merged = merged.merge(r2_map, on=["market_id", "player_2"], how="left")

    # Join LTP odds for both players
    ltp1 = ltps.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"})
    ltp2 = ltps.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"})

    merged = merged.merge(ltp1, on=["market_id", "selection_id_1"], how="left")
    merged = merged.merge(ltp2, on=["market_id", "selection_id_2"], how="left")

    # Clean final output
    merged = merged.drop(columns=["selection_id_1", "selection_id_2"], errors="ignore")
    merged.to_csv(output_csv, index=False)
    print(f"✅ Merged {len(merged)} enriched match rows to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    merge_matches_with_ltps(args.match_csv, args.snapshots_csv, args.ltps_csv, args.output_csv)
