import argparse
import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

from scripts.utils.snapshot_parser import SnapshotParser
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import should_run

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--mode", choices=["full", "ltp_only", "metadata"], default="full")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    root = Path(args.input_dir)
    all_files = list(root.rglob("*.bz2"))

    parser_obj = SnapshotParser(mode=args.mode)
    filtered_files = [f for f in all_files if parser_obj.should_parse_file(f, start, end)]
    log_info(f"🔍 Found {len(filtered_files)} .bz2 files in range")

    all_records = []
    failed_files = []

    for file in tqdm(filtered_files, desc="Parsing files"):
        try:
            log_info(f"📂 Parsing: {file}")
            all_records.extend(parser_obj.parse_file(file))
        except Exception as e:
            log_warning(f"⚠️ Failed to parse {file}: {e}")
            failed_files.append(str(file))

    if not all_records:
        log_warning("⚠️ No records extracted.")
        return

    df = pd.DataFrame(all_records)

    if args.mode != "metadata":
        df = df.dropna(subset=["selection_id"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")

    df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    log_success(f"✅ Saved {len(df)} rows to {args.output_csv}")

    if failed_files:
        log_warning(f"⚠️ Failed files: {len(failed_files)}")
        for f in failed_files[:5]:
            log_warning(f"   → {f}")
        if len(failed_files) > 5:
            log_warning(f"   ... and {len(failed_files) - 5} more")

if __name__ == "__main__":
    main()
