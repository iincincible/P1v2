import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    args = parser.parse_args()

    match_df = pd.read_csv(args.match_csv)
    snap_df = pd.read_csv(args.snapshots_csv)

    print(f"\n📂 Match file: {args.match_csv}")
    print(f"📂 Snapshot file: {args.snapshots_csv}")

    total_matches = len(match_df)
    with_ids = match_df["selection_id_1"].notna() & match_df["selection_id_2"].notna()
    with_odds = match_df["odds_player_1"].notna() & match_df["odds_player_2"].notna()
    with_winner = match_df["actual_winner"].notna()

    print(f"\n📊 Match coverage:")
    print(f" - Total matches: {total_matches}")
    print(f" - With selection IDs: {with_ids.sum()} ({with_ids.mean():.1%})")
    print(f" - With odds: {with_odds.sum()} ({with_odds.mean():.1%})")
    print(f" - With winner label: {with_winner.sum()} ({with_winner.mean():.1%})")

    final_snap = snap_df.copy()
    final_snap["market_id"] = final_snap["market_id"].astype(str)
    final_snap["selection_id"] = pd.to_numeric(final_snap["selection_id"], errors="coerce").astype("Int64")
    final_snap = final_snap.dropna(subset=["ltp", "runner_name", "timestamp"])
    final_snap = final_snap.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")

    snap_markets = final_snap["market_id"].nunique()
    print(f" - Snapshots with final LTP: {len(final_snap)} runners from {snap_markets} markets")

if __name__ == "__main__":
    main()
