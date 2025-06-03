import pandas as pd
import argparse

def build_match_level_dataset(merged_csv, snapshots_csv, output_csv):
    print(f"🔍 Reading merged match data from {merged_csv}")
    merged = pd.read_csv(merged_csv)
    merged = merged.dropna(subset=["market_id", "selection_id_1", "selection_id_2", "winner_name"])
    merged = merged.drop_duplicates(subset=["market_id"])

    print(f"🔍 Reading snapshots from {snapshots_csv}")
    snaps = pd.read_csv(snapshots_csv)
    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp"])

    # Get latest snapshot per market/selection_id
    snaps = snaps.sort_values("timestamp").drop_duplicates(subset=["market_id", "selection_id"], keep="last")

    # Merge in odds for player 1
    merged = merged.merge(
        snaps[["market_id", "selection_id", "ltp"]].rename(
            columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}
        ),
        on=["market_id", "selection_id_1"],
        how="left"
    )

    # Merge in odds for player 2
    merged = merged.merge(
        snaps[["market_id", "selection_id", "ltp"]].rename(
            columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}
        ),
        on=["market_id", "selection_id_2"],
        how="left"
    )

    # Drop rows missing odds
    merged = merged.dropna(subset=["odds_player_1", "odds_player_2", "player_1", "player_2"])

    # Calculate margin and implied probabilities
    merged["odds_margin"] = 1 / merged["odds_player_1"] + 1 / merged["odds_player_2"]
    merged["implied_prob_1"] = (1 / merged["odds_player_1"]) / merged["odds_margin"]
    merged["implied_prob_2"] = (1 / merged["odds_player_2"]) / merged["odds_margin"]
    merged["implied_diff"] = merged["implied_prob_1"] - merged["implied_prob_2"]

    # Create target variable
    merged["won"] = (merged["player_1"] == merged["winner_name"]).astype(int)

    print(f"✅ Final match-level training rows: {len(merged)}")
    print(merged["won"].value_counts())

    merged.to_csv(output_csv, index=False)
    print(f"✅ Saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True, help="Enriched match file with player names and winner_name")
    parser.add_argument("--snapshots_csv", required=True, help="Parsed snapshot LTPs file")
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    build_match_level_dataset(args.merged_csv, args.snapshots_csv, args.output_csv)
