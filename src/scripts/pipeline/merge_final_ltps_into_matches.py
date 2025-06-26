# File: src/scripts/pipeline/merge_final_ltps_into_matches.py

import argparse
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def merge_final_ltps(
    matches_csv,
    snapshots_csv,
    output_csv,
    max_missing_frac=0.1,  # Halt if >10% missing LTPs unless --ignore_missing
    drop_missing_rows=False,
    ignore_missing=False,
    overwrite=False,
    dry_run=False,
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

    # Log missing values summary
    n_missing_1 = matches["ltp_player_1"].isnull().sum()
    n_missing_2 = matches["ltp_player_2"].isnull().sum()
    total = len(matches)
    frac1 = n_missing_1 / total if total > 0 else 0
    frac2 = n_missing_2 / total if total > 0 else 0

    if n_missing_1 or n_missing_2:
        logging.warning(
            f"⚠️ {n_missing_1} (player 1) and {n_missing_2} (player 2) LTP values missing after merge."
        )
        halt = (frac1 > max_missing_frac) or (frac2 > max_missing_frac)
        if halt and not ignore_missing:
            logging.error(
                f"❌ Too many missing LTPs (> {max_missing_frac:.0%}). Halting. Use --ignore_missing to proceed anyway."
            )
            return

    # Optionally drop rows with missing LTPs
    if drop_missing_rows:
        before = len(matches)
        matches = matches.dropna(subset=["ltp_player_1", "ltp_player_2"])
        dropped = before - len(matches)
        logging.info(
            f"🧹 Dropped {dropped} rows with missing LTPs (now {len(matches)} rows)"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    matches.to_csv(output_path, index=False)
    logging.info(f"✅ Saved matches with LTPs to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Merge final LTPs into matches.")
    parser.add_argument("--matches_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument(
        "--max_missing_frac",
        type=float,
        default=0.1,
        help="Halt if missing LTPs above this fraction (default 0.1)",
    )
    parser.add_argument(
        "--drop_missing_rows", action="store_true", help="Drop rows with missing LTPs"
    )
    parser.add_argument(
        "--ignore_missing",
        action="store_true",
        help="Ignore halt on missing LTPs, just warn",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    merge_final_ltps(
        matches_csv=args.matches_csv,
        snapshots_csv=args.snapshots_csv,
        output_csv=args.output_csv,
        max_missing_frac=args.max_missing_frac,
        drop_missing_rows=args.drop_missing_rows,
        ignore_missing=args.ignore_missing,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
