import argparse
import pandas as pd

def merge_ltps_by_ids(merged_csv, ltps_csv, output_csv):
    # Load merged match data
    df = pd.read_csv(merged_csv, low_memory=False)
    df = df.dropna(subset=["selection_id_1", "selection_id_2"])
    print(f"🔎 Filtered to {len(df):,} rows with both selection IDs")

    # Normalize ID types
    df["selection_id_1"] = pd.to_numeric(df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
    df["selection_id_2"] = pd.to_numeric(df["selection_id_2"], errors="coerce").astype("Int64").astype(str)
    df["market_id"] = df["market_id"].astype(str)

    # Load snapshot file
    ltps = pd.read_csv(ltps_csv, low_memory=False)
    ltps["selection_id"] = pd.to_numeric(ltps["selection_id"], errors="coerce")
    ltps["market_id"] = ltps["market_id"].astype(str)
    ltps["selection_id"] = ltps["selection_id"].astype("Int64").astype(str)
    ltps["timestamp"] = pd.to_datetime(ltps["timestamp"], errors="coerce")
    ltps = ltps.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
    ltps_clean = ltps[["market_id", "selection_id", "ltp"]].dropna(subset=["ltp"])

    # Drop any preexisting odds columns
    df = df.drop(columns=[c for c in df.columns if c.startswith("odds_player_")], errors="ignore")

    # Merge LTPs
    df = df.merge(
        ltps_clean.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}),
        on=["market_id", "selection_id_1"], how="left"
    )
    df = df.merge(
        ltps_clean.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}),
        on=["market_id", "selection_id_2"], how="left"
    )

    # Validate
    before = len(df)
    df = df.dropna(subset=["odds_player_1", "odds_player_2"])
    after = len(df)
    print(f"✅ Merged LTPs for {after:,} / {before:,} rows")

    df.to_csv(output_csv, index=False)
    print(f"📁 Saved patched output to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()
    merge_ltps_by_ids(args.merged_csv, args.ltps_csv, args.output_csv)

if __name__ == "__main__":
    main()
