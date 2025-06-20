import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from scripts.utils.logger import log_info, log_success, log_error, log_dryrun
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists
from scripts.utils.snapshot_parser import SnapshotParser


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

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would parse snapshots in {_args.input_dir} from {_args.start_date} to {_args.end_date} "
            f"in mode {_args.mode} → {_args.output_csv}"
        )
        return

    input_path = Path(_args.input_dir)
    output_path = Path(_args.output_csv)
    assert_file_exists(input_path, "input_dir")
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    parser_obj = SnapshotParser(mode=_args.mode)
    try:
        start = datetime.strptime(_args.start_date, "%Y-%m-%d")
        end = datetime.strptime(_args.end_date, "%Y-%m-%d")
    except Exception as e:
        log_error(f"❌ Invalid date format: {e}")
        return

    try:
        rows = parser_obj.parse_directory(_args.input_dir, start=start, end=end)
    except Exception as e:
        log_error(f"❌ Error parsing snapshots: {e}")
        return

    if not rows:
        log_error("❌ No snapshot data extracted.")
        return

    try:
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"✅ Saved {len(df)} snapshot rows to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save parsed snapshots: {e}")


if __name__ == "__main__":
    main()
