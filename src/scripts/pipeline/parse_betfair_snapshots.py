import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from scripts.utils.logger import log_info, log_success, log_error, log_dryrun
from scripts.utils.cli_utils import add_common_flags, assert_file_exists, should_run, output_file_guard
from scripts.utils.snapshot_parser import SnapshotParser

@output_file_guard(output_arg="output_csv")
def parse_betfair_snapshots(
    input_dir,
    output_csv,
    start_date,
    end_date,
    mode="final",
    overwrite=False,
    dry_run=False,
):
    assert_file_exists(input_dir, "input_dir")

    parser_obj = SnapshotParser(mode=mode)
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        log_error(f"❌ Invalid date format: {e}")
        return

    try:
        rows = parser_obj.parse_directory(input_dir, start=start, end=end)
    except Exception as e:
        log_error(f"❌ Error parsing snapshots: {e}")
        return

    if not rows:
        log_error("❌ No snapshot data extracted.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    log_success(f"✅ Saved {len(df)} snapshot rows to {output_csv}")

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Parse Betfair snapshots to structured CSV."
    )
    parser.add_argument(
        "--input_dir", required=True, help="Directory with .bz2 snapshot files"
    )
    parser.add_argument(
        "--output_csv", required=True, help="Path to save parsed snapshot data"
    )
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--mode", choices=["final", "full", "metadata"], default="final"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)
    parse_betfair_snapshots(
        input_dir=_args.input_dir,
        output_csv=_args.output_csv,
        start_date=_args.start_date,
        end_date=_args.end_date,
        mode=_args.mode,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
