import argparse
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from scripts.utils.logger import (
    log_info,
    log_warning,
    log_success,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.snapshot_parser import SnapshotParser

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Scan and extract candidate ATP tournament markets from Betfair snapshots."
    )
    parser.add_argument(
        "--input_dir", required=True, help="Directory containing .bz2 snapshot files"
    )
    parser.add_argument(
        "--output_csv", required=True, help="File path to save extracted metadata"
    )
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would scan { _args.input_dir } from { _args.start_date } to { _args.end_date } "
            f"→ { _args.output_csv }"
        )
        return

    input_path = Path(_args.input_dir)
    output_path = Path(_args.output_csv)

    # Pre-flight checks
    assert_file_exists(input_path, "input_dir")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    try:
        start = datetime.strptime(_args.start_date, "%Y-%m-%d")
        end = datetime.strptime(_args.end_date, "%Y-%m-%d")
    except Exception as e:
        log_error(f"❌ Invalid date format: {e}")
        return

    parser_obj = SnapshotParser(mode="metadata")
    all_files = list(input_path.rglob("*.bz2"))
    filtered = [f for f in all_files if parser_obj.should_parse_file(f, start, end)]
    log_info(f"🔍 Found {len(filtered)} .bz2 files in range")

    all_rows = []
    for f in tqdm(filtered, desc="Extracting metadata"):
        try:
            rows = parser_obj.parse_file(f)
            all_rows.extend(rows)
        except Exception as e:
            log_warning(f"⚠️ Failed to parse {f}: {e}")

    if not all_rows:
        log_warning("⚠️ No metadata rows found.")
        return

    try:
        df = pd.DataFrame(all_rows)
        df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")
        df = df.dropna(subset=["runner_1", "runner_2", "market_id"])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"✅ Saved {len(df)} ATP candidate markets to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save metadata CSV: {e}")

if __name__ == "__main__":
    main()
