import pandas as pd
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True, help="Match file with selection_id_1/2 and market_id")
    parser.add_argument("--snapshots_csv", required=True, help="Snapshot file with final LTPs")
    parser.add_argument("--output_csv", required=True, help="Path to save match file with odds_player_1/2")
    args = parser.parse_args()

    # === Load match file
    match_df = pd.read_csv(args.match_csv)
    match_df["market_id"] = match_df["market_id"].astype(str)
    match_df["selection_id_1"] = pd.to_numeric(match_df["selection_id_1"], errors="coerce").astype("Int64")
    match_df["selection_id_2"] = pd.to_numeric(match_df["selection_id_2"], errors="coerce").astype("Int64")

    # === Load snapshot file and reduce to final snapshot per runner
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp", "timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64")
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps = snaps.sort_values("timestamp")
    latest = snaps.drop_duplicates(["market_id", "selection_id"], keep="last")[["market_id", "selection_id", "ltp"]]

    # === Merge LTPs into matches
    merged = match_df.merge(
        latest.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}),
        on=["market_id", "selection_id_1"],
        how="left"
    ).merge(
        latest.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}),
        on=["market_id", "selection_id_2"],
        how="left"
    )

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output_csv, index=False)

    # === Report
    total = len(merged)
    valid = merged["odds_player_1"].notna() & merged["odds_player_2"].notna()
    matched = valid.sum()
    print(f"✅ Saved {total} rows to {args.output_csv}")
    print(f"📊 LTP odds matched for {matched} of {total} rows ({matched / total:.1%})")

if __name__ == "__main__":
    main()
