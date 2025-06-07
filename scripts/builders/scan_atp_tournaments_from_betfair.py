import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from scripts.utils.snapshot_parser import SnapshotParser
from scripts.utils.logger import log_info, log_warning, log_success
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists


def main():
    parser = argparse.ArgumentParser(description="Scan and extract candidate ATP tournament markets from Betfair snapshots.")
    parser.add_argument("--input_dir", required=True, help="Directory containing .bz2 snapshot files")
    parser.add_argument("--output_csv", required=True, help="File path to save extracted metadata")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    all_files = list(Path(args.input_dir).rglob("*.bz2"))
    parser_obj = SnapshotParser(mode="metadata")

    filtered = [f for f in all_files if parser_obj.should_parse_file(f, start, end)]
    log_info(f"🔍 Found {len(filtered)} .bz2 files in range")

    all_rows = []
    for f in tqdm(filtered, desc="Extracting metadata"):
        all_rows.extend(parser_obj.parse_file(f))

    if not all_rows:
        log_warning("⚠️ No metadata rows found.")
        return

    df = pd.DataFrame(all_rows)
    df["market_time"] = pd.to_datetime(df["market_time"], errors="coerce")
    df = df.dropna(subset=["runner_1", "runner_2", "market_id"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_success(f"✅ Saved {len(df)} ATP candidate markets to {output_path}")


if __name__ == "__main__":
    main()
