import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from scripts.utils.snapshot_parser import SnapshotParser
from scripts.utils.logger import log_info, log_success
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists


def main():
    parser = argparse.ArgumentParser(description="Parse Betfair snapshots to structured CSV.")
    parser.add_argument("--input_dir", required=True, help="Directory with .bz2 snapshot files")
    parser.add_argument("--output_csv", required=True, help="Path to save parsed snapshot data")
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--mode", choices=["final", "full", "metadata"], default="final")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)
    if not should_run(output_path, args.overwrite, args.dry_run):
        return
    assert_file_exists(args.input_dir, "input_dir")

    parser_obj = SnapshotParser(mode=args.mode)
    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    rows = parser_obj.parse_directory(args.input_dir, start=start, end=end)
    if not rows:
        raise ValueError("❌ No snapshot data extracted.")

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_success(f"✅ Saved {len(df)} snapshot rows to {output_path}")


if __name__ == "__main__":
    main()
