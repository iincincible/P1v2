import yaml
import subprocess
from pathlib import Path
import sys
import time
import os

from scripts.utils.paths import get_pipeline_paths, get_snapshot_csv_path
from scripts.utils.cli_utils import assert_file_exists, add_common_flags, merge_with_defaults
from scripts.utils.logger import log_info, log_success, log_warning, log_error

PYTHON = sys.executable
CONFIG_FILE = "configs/tournaments_2024.yaml"
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"
SNAPSHOT_SCRIPT = "scripts/pipeline/parse_betfair_snapshots.py"
BETFAIR_DATA_DIR = "data/BASIC"


def parse_snapshots_if_needed(conf, overwrite=False, dry_run=False) -> str:
    label = conf["label"]
    snapshot_csv = conf.get("snapshots_csv") or get_snapshot_csv_path(label)
    conf["snapshots_csv"] = snapshot_csv

    start = conf.get("start_date", "2023-01-01")
    end = conf.get("end_date", "2023-12-31")

    if Path(snapshot_csv).exists() and not overwrite:
        log_info(f"🟢 Snapshots already exist: {snapshot_csv}")
        return snapshot_csv

    if dry_run:
        log_info(f"🧪 Dry run: would generate snapshots for {label} → {snapshot_csv}")
        return snapshot_csv

    log_info(f"📦 Generating snapshots for: {label}")
    cmd = [
        PYTHON, SNAPSHOT_SCRIPT,
        "--input_dir", BETFAIR_DATA_DIR,
        "--output_csv", snapshot_csv,
        "--start_date", start,
        "--end_date", end,
        "--mode", "full",
        "--overwrite"
    ]

    try:
        t0 = time.perf_counter()
        subprocess.run(cmd, check=True, env={**dict(**os.environ), "PYTHONPATH": "."})
        t1 = time.perf_counter()
        log_success(f"✅ Parsed snapshots to {snapshot_csv} in {t1 - t0:.2f} seconds")
    except subprocess.CalledProcessError as e:
        log_error(f"❌ Snapshot parsing failed for {label}")
        log_error(f"    Command: {' '.join(cmd)}")
        raise

    return snapshot_csv


def main():
    parser = argparse.ArgumentParser(description="Build raw matches for all tournaments in YAML config.")
    parser.add_argument("--config", default=CONFIG_FILE, help="Path to tournaments YAML config")
    add_common_flags(parser)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    defaults = config.get("defaults", {})
    tournaments = config.get("tournaments", [])

    for t in tournaments:
        conf = merge_with_defaults(t, defaults)
        label = conf["label"]
        log_info(f"\n🏗️ Building: {label}")
        try:
            snapshot_csv = parse_snapshots_if_needed(conf, overwrite=args.overwrite, dry_run=args.dry_run)

            output_path = get_pipeline_paths(label)["raw_csv"]
            if output_path.exists() and not args.overwrite:
                log_info(f"⏭️ Output already exists: {output_path}")
                continue

            if args.dry_run:
                log_info(f"🧪 Dry run: would run {BUILDER_SCRIPT} for {label} → {output_path}")
                continue

            assert_file_exists(snapshot_csv, "snapshots_csv")
            if conf.get("sackmann_csv") and not conf.get("snapshot_only", False):
                assert_file_exists(conf["sackmann_csv"], "sackmann_csv")
            if "alias_csv" in conf:
                assert_file_exists(conf["alias_csv"], "alias_csv")

            cmd = [
                PYTHON, BUILDER_SCRIPT,
                "--tour", conf["tour"],
                "--tournament", conf["tournament"],
                "--year", str(conf["year"]),
                "--snapshots_csv", conf["snapshots_csv"],
                "--output_csv", str(output_path),
                "--overwrite"
            ]

            if conf.get("sackmann_csv") and not conf.get("snapshot_only", False):
                cmd += ["--sackmann_csv", conf["sackmann_csv"]]
            if conf.get("snapshot_only"):
                cmd.append("--snapshot_only")
            if conf.get("fuzzy_match"):
                cmd.append("--fuzzy_match")
            if "alias_csv" in conf:
                cmd += ["--alias_csv", conf["alias_csv"]]

            t0 = time.perf_counter()
            subprocess.run(cmd, check=True)
            t1 = time.perf_counter()
            log_success(f"✅ Finished: {label} in {t1 - t0:.2f} seconds")
        except Exception as e:
            log_error(f"⚠️ Skipping {label} due to error: {e}")


if __name__ == "__main__":
    main()
