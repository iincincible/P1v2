import pandas as pd
from pathlib import Path
import argparse

def fallback_fill_with_runner_name(merged_df, snaps_df):
    # Ensure LTP columns exist
    if "odds_player_1" not in merged_df.columns:
        merged_df["odds_player_1"] = None
    if "odds_player_2" not in merged_df.columns:
        merged_df["odds_player_2"] = None

    # Normalize names for matching
    def norm(x): return str(x).lower().replace(".", "").replace("-", " ").strip()

    snaps_df = snaps_df.dropna(subset=["market_id", "selection_id", "ltp", "runner_name"])
    snaps_df["market_id"] = snaps_df["market_id"].astype(str)
    snaps_df["runner_clean"] = snaps_df["runner_name"].map(norm)

    for idx, row in merged_df.iterrows():
        if pd.isna(row["odds_player_1"]) and pd.notna(row.get("player_1")):
            mc = norm(row["player_1"])
            snapshot_match = snaps_df[
                (snaps_df["market_id"] == row["market_id"]) &
                (snaps_df["runner_clean"] == mc)
            ]
            if not snapshot_match.empty:
                merged_df.at[idx, "odds_player_1"] = snapshot_match.sort_values("timestamp").iloc[-1]["ltp"]

        if pd.isna(row["odds_player_2"]) and pd.notna(row.get("player_2")):
            mc = norm(row["player_2"])
            snapshot_match = snaps_df[
                (snaps_df["market_id"] == row["market_id"]) &
                (snaps_df["runner_clean"] == mc)
            ]
            if not snapshot_match.empty:
                merged_df.at[idx, "odds_player_2"] = snapshot_match.sort_values("timestamp").iloc[-1]["ltp"]

    return merged_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    # Load matches
    match_df = pd.read_csv(args.match_csv)
    match_df["market_id"] = match_df["market_id"].astype(str)
    match_df["selection_id_1"] = pd.to_numeric(match_df["selection_id_1"], errors="coerce").astype("Int64")
    match_df["selection_id_2"] = pd.to_numeric(match_df["selection_id_2"], errors="coerce").astype("Int64")

    # Load and clean snapshots
    snaps = pd.read_csv(args.snapshots_csv)
    snaps = snaps.dropna(subset=["market_id", "selection_id", "ltp", "timestamp"])
    snaps["market_id"] = snaps["market_id"].astype(str)
    snaps["selection_id"] = pd.to_numeric(snaps["selection_id"], errors="coerce").astype("Int64")
    snaps["timestamp"] = pd.to_datetime(snaps["timestamp"])
    snaps = snaps.sort_values("timestamp")

    latest = snaps.drop_duplicates(["market_id", "selection_id"], keep="last")[["market_id", "selection_id", "ltp"]]

    # Merge by selection ID
    merged = match_df.merge(
        latest.rename(columns={"selection_id": "selection_id_1", "ltp": "odds_player_1"}),
        on=["market_id", "selection_id_1"],
        how="left"
    ).merge(
        latest.rename(columns={"selection_id": "selection_id_2", "ltp": "odds_player_2"}),
        on=["market_id", "selection_id_2"],
        how="left"
    )

    # Fallback fill by runner name
    merged = fallback_fill_with_runner_name(merged, snaps)

    # Save
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(merged)} rows to {args.output_csv}")

    # Diagnostics
    num_missing = merged["odds_player_1"].isna().sum() + merged["odds_player_2"].isna().sum()
    print(f"⚠️ Final missing LTPs after fallback: {num_missing} of {2 * len(merged)}")

if __name__ == "__main__":
    main()
