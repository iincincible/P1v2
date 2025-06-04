import pandas as pd
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repaired_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    # === Load repaired match file
    df = pd.read_csv(args.repaired_csv)
    print(f"✨ Loaded {len(df)} repaired matches")

    # === Load snapshot data
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp", "timestamp"])

    # Keep latest LTP per market_id + selection_id
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps = snaps.sort_values("timestamp")
    latest = snaps.groupby(["market_id", "selection_id"]).last().reset_index()
    latest = latest[["market_id", "selection_id", "ltp"]]

    # === Merge LTPs into match file
    df["market_id"] = df["market_id"].astype(str)
    latest["market_id"] = latest["market_id"].astype(str)

    df = df.merge(
        latest.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}),
        on=["market_id", "selection_id_1"],
        how="left"
    )

    df = df.merge(
        latest.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}),
        on=["market_id", "selection_id_2"],
        how="left"
    )

    # === Save patched output
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved LTP-enriched match file to {args.output_csv}")
    print(df[["odds_player_1", "odds_player_2"]].notnull().sum())

if __name__ == "__main__":
    main()
