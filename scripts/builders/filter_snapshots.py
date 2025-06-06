import pandas as pd
import argparse
from pathlib import Path
from tqdm import tqdm
from thefuzz import fuzz
from scripts.utils.logger import log_info, log_success, log_warning

def filter_by_market_ids(match_csv, snapshots_csv, output_csv):
    log_info("Filtering by market_id")
    match_df = pd.read_csv(match_csv, usecols=["market_id"])
    match_df["market_id"] = match_df["market_id"].astype(str)
    valid_ids = match_df["market_id"].dropna().unique()

    snap_df = pd.read_csv(snapshots_csv)
    snap_df["market_id"] = snap_df["market_id"].astype(str)
    filtered = snap_df[snap_df["market_id"].isin(valid_ids)].copy()

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output_csv, index=False)
    log_success(f"Saved {len(filtered)} snapshot rows with valid market_ids to {output_csv}")

def filter_by_selection_ids(match_csv, snapshots_csv, output_csv):
    log_info("Filtering by selection_id presence")
    match_df = pd.read_csv(match_csv)
    match_df["market_id"] = match_df["market_id"].astype(str)
    match_df["selection_id_1"] = pd.to_numeric(match_df["selection_id_1"], errors="coerce").astype("Int64").astype(str)
    match_df["selection_id_2"] = pd.to_numeric(match_df["selection_id_2"], errors="coerce").astype("Int64").astype(str)

    id_keys = set(zip(match_df["market_id"], match_df["selection_id_1"])) | \
              set(zip(match_df["market_id"], match_df["selection_id_2"]))

    snap_df = pd.read_csv(snapshots_csv)
    snap_df["market_id"] = snap_df["market_id"].astype(str)
    snap_df["selection_id"] = pd.to_numeric(snap_df["selection_id"], errors="coerce").astype("Int64").astype(str)
    snap_df["timestamp"] = pd.to_datetime(snap_df["timestamp"], errors="coerce")
    snap_df = snap_df.sort_values("timestamp").drop_duplicates(["market_id", "selection_id"], keep="last")
    valid_keys = set(zip(snap_df["market_id"], snap_df["selection_id"]))

    filtered_df = match_df[
        match_df.apply(
            lambda row: (row["market_id"], row["selection_id_1"]) in valid_keys and
                        (row["market_id"], row["selection_id_2"]) in valid_keys,
            axis=1
        )
    ]

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_csv, index=False)
    log_success(f"Saved {len(filtered_df)} match rows with valid selection_ids to {output_csv}")

def filter_by_player_names(match_csv, snapshots_csv, output_csv):
    log_info("Filtering by player names (fuzzy match)")
    matches = pd.read_csv(match_csv)
    matches["match_date"] = pd.to_datetime(matches["tourney_date"], errors="coerce")
    player_names = set(matches["winner_name"].dropna().tolist() + matches["loser_name"].dropna().tolist())
    player_names = [p.lower() for p in player_names]

    snaps = pd.read_csv(snapshots_csv)
    snaps["market_time"] = pd.to_datetime(snaps["market_time"], errors="coerce")
    snaps["runner_clean"] = snaps["runner_name"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
    snaps = snaps.dropna(subset=["runner_clean", "market_time"])

    matched_rows = []
    for _, snap_row in tqdm(snaps.iterrows(), total=len(snaps), desc="🧠 Fuzzy matching"):
        runner = snap_row["runner_clean"]
        if any(fuzz.partial_ratio(runner, p) >= 85 for p in player_names):
            matched_rows.append(snap_row)

    out_df = pd.DataFrame(matched_rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    log_success(f"Saved {len(out_df)} fuzzy-matched snapshot rows to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["market_ids", "selection_ids", "player_names"])
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    if args.mode == "market_ids":
        filter_by_market_ids(args.match_csv, args.snapshots_csv, args.output_csv)
    elif args.mode == "selection_ids":
        filter_by_selection_ids(args.match_csv, args.snapshots_csv, args.output_csv)
    elif args.mode == "player_names":
        filter_by_player_names(args.match_csv, args.snapshots_csv, args.output_csv)

if __name__ == "__main__":
    main()
    