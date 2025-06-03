import pandas as pd
import argparse
from difflib import get_close_matches

def standardize(name):
    return str(name).lower().replace(".", "").replace("-", " ").strip()

def get_closest_selection_id(player, market_id, snaps_grouped):
    if market_id not in snaps_grouped:
        return None
    options = snaps_grouped[market_id]
    matches = get_close_matches(standardize(player), [standardize(x[1]) for x in options], n=1, cutoff=0.8)
    if not matches:
        return None
    for sel_id, runner_name in options:
        if standardize(runner_name) == standardize(matches[0]):
            return sel_id
    return None

def patch_merge_with_ltps(merged_csv, ltps_csv, output_csv):
    print(f"🔍 Reading merged: {merged_csv}")
    merged = pd.read_csv(merged_csv)
    merged = merged.dropna(subset=["player_1", "player_2", "market_id"])

    print(f"🔍 Reading LTP snapshots: {ltps_csv}")
    ltps = pd.read_csv(ltps_csv)

    # Fix for your data structure
    ltps = ltps.dropna(subset=["market_id", "selection_id", "selection_name", "ltp"])
    ltps = ltps.rename(columns={"selection_name": "runner_name"})

    # Get final snapshot per runner per market
    ltps_latest = ltps.sort_values("timestamp").drop_duplicates(subset=["market_id", "selection_id"], keep="last")

    # Group runners by market for fuzzy matching
    grouped = ltps_latest.groupby("market_id")[["selection_id", "runner_name"]].apply(
        lambda df: list(df.itertuples(index=False, name=None))
    ).to_dict()

    print("🔁 Fuzzy-matching runner names...")
    merged["selection_id_1"] = merged.apply(
        lambda row: get_closest_selection_id(row["player_1"], row["market_id"], grouped), axis=1)
    merged["selection_id_2"] = merged.apply(
        lambda row: get_closest_selection_id(row["player_2"], row["market_id"], grouped), axis=1)

    before = len(merged)
    merged = merged.dropna(subset=["selection_id_1", "selection_id_2"])
    after = len(merged)
    print(f"✅ Matched selection IDs for {after}/{before} rows")

    # Merge in LTPs
    merged = merged.merge(
        ltps_latest[["market_id", "selection_id", "ltp"]].rename(
            columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}
        ),
        on=["market_id", "selection_id_1"],
        how="left"
    )

    merged = merged.merge(
        ltps_latest[["market_id", "selection_id", "ltp"]].rename(
            columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}
        ),
        on=["market_id", "selection_id_2"],
        how="left"
    )

    # Drop rows with missing odds
    merged = merged.dropna(subset=["odds_player_1", "odds_player_2"])

    print(f"✅ Patched {len(merged)} rows with LTPs and selection IDs")
    merged.to_csv(output_csv, index=False)
    print(f"✅ Saved to: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    patch_merge_with_ltps(args.merge_csv, args.ltps_csv, args.output_csv)
