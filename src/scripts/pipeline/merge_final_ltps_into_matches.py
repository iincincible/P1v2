import argparse
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def merge_final_ltps(
    matches_csv, snapshots_csv, output_csv, overwrite=False, dry_run=False
):
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logging.info(f"[SKIP] {output_csv} exists and --overwrite not set")
        return

    matches = pd.read_csv(matches_csv)
    logging.info(f"📥 Loaded {len(matches)} matches from {matches_csv}")
    snapshots = pd.read_csv(snapshots_csv)
    logging.info(f"📥 Loaded {len(snapshots)} snapshots from {snapshots_csv}")

    # Sort snapshots and get last LTP per (market_id, selection_id)
    snapshots_sorted = snapshots.sort_values("timestamp")
    last_ltps = (
        snapshots_sorted.groupby(["market_id", "selection_id"])["ltp"]
        .last()
        .reset_index()
    )

    # Merge for player 1
    matches = matches.merge(
        last_ltps.rename(
            columns={"selection_id": "selection_id_1", "ltp": "ltp_player_1"}
        ),
        on=["market_id", "selection_id_1"],
        how="left",
    )

    # Merge for player 2
    matches = matches.merge(
        last_ltps.rename(
            columns={"selection_id": "selection_id_2", "ltp": "ltp_player_2"}
        ),
        on=["market_id", "selection_id_2"],
        how="left",
    )

    # Log missing values
    for col in ["ltp_player_1", "ltp_player_2"]:
        n_missing = matches[col].isnull().sum()
        if n_missing > 0:
            logging.warning(f"⚠️ {n_missing} {col} values are missing after merge")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    matches.to_csv(output_path, index=False)
    logging.info(f"✅ ✅ Saved matches with LTPs to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Merge final LTPs into matches.")
    parser.add_argument("--matches_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    merge_final_ltps(
        matches_csv=args.matches_csv,
        snapshots_csv=args.snapshots_csv,
        output_csv=args.output_csv,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
