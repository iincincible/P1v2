# File: src/scripts/pipeline/merge_final_ltps_into_matches.py

import argparse
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def merge_final_ltps(
    matches_csv: str,
    snapshots_csv: str,
    output_csv: str,
    max_missing_frac: float = 0.1,  # Halt if >10% missing LTPs unless --ignore_missing
    drop_missing_rows: bool = False,
    ignore_missing: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
):
    """
    Merge final LTPs into the matches dataframe.

    - Drops legacy list-columns from matches.
    - Computes last LTP per (market_id, selection_id) from snapshots.
    - Merges ltp_player_1 and ltp_player_2.
    - Coerces LTP columns to floats, reports missing values.
    - Optionally drops rows missing LTPs.
    """
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        logging.info(f"[SKIP] {output_csv} exists and --overwrite not set")
        return

    # Dry-run only
    if dry_run:
        logging.info(f"[DRY-RUN] Would write: {output_csv}")
        return

    # Load input data
    matches = pd.read_csv(matches_csv)
    logging.info(f"📥 Loaded {len(matches)} matches from {matches_csv}")
    snapshots = pd.read_csv(snapshots_csv)
    logging.info(f"📥 Loaded {len(snapshots)} snapshots from {snapshots_csv}")

    # Sort and compute last traded price per runner
    snapshots_sorted = snapshots.sort_values("timestamp")
    last_ltps = (
        snapshots_sorted.groupby(["market_id", "selection_id"])["ltp"]
        .last()
        .reset_index()
    )

    # Drop legacy list-columns to avoid merging list or string lists
    for col in ["selection_id", "ltp", "runner_name", "timestamp"]:
        if col in matches.columns:
            matches.drop(columns=[col], inplace=True)

    # Merge LTP for player 1
    matches = matches.merge(
        last_ltps.rename(
            columns={"selection_id": "selection_id_1", "ltp": "ltp_player_1"}
        ),
        on=["market_id", "selection_id_1"],
        how="left",
    )

    # Merge LTP for player 2
    matches = matches.merge(
        last_ltps.rename(
            columns={"selection_id": "selection_id_2", "ltp": "ltp_player_2"}
        ),
        on=["market_id", "selection_id_2"],
        how="left",
    )

    # Coerce LTP columns to floats
    matches["ltp_player_1"] = pd.to_numeric(matches["ltp_player_1"], errors="coerce")
    matches["ltp_player_2"] = pd.to_numeric(matches["ltp_player_2"], errors="coerce")

    # Report missing LTPs
    total = len(matches)
    n_missing_1 = matches["ltp_player_1"].isna().sum()
    n_missing_2 = matches["ltp_player_2"].isna().sum()
    frac1 = n_missing_1 / total if total else 0
    frac2 = n_missing_2 / total if total else 0
    if n_missing_1 or n_missing_2:
        logging.warning(
            f"⚠️ {n_missing_1} (player 1) and {n_missing_2} (player 2) LTP values missing after merge."
        )
        if (
            frac1 > max_missing_frac or frac2 > max_missing_frac
        ) and not ignore_missing:
            logging.error(
                f"❌ Too many missing LTPs (> {max_missing_frac:.0%}). Halting. Use --ignore_missing to proceed anyway."
            )
            return

    # Optionally drop rows lacking either LTP
    if drop_missing_rows:
        before = total
        matches = matches.dropna(subset=["ltp_player_1", "ltp_player_2"]).reset_index(
            drop=True
        )
        dropped = before - len(matches)
        logging.info(
            f"🧹 Dropped {dropped} rows with missing LTPs. Remaining: {len(matches)} rows."
        )

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matches.to_csv(output_csv, index=False)
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
