import argparse
import subprocess
import sys
import time
import os
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run
from scripts.utils.config_validation import validate_yaml, TOURNAMENTS_SCHEMA
from scripts.utils.paths import get_pipeline_paths, get_snapshot_csv_path

PYTHON = sys.executable
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"
SNAPSHOT_SCRIPT = "scripts/pipeline/parse_betfair_snapshots.py"
BETFAIR_DATA_DIR = "data/BASIC"


def parse_snapshots_if_needed(conf: dict, overwrite: bool, dry_run: bool) -> str:
    label = conf["label"]
    snapshot_csv = conf.get("snapshots_csv") or get_snapshot_csv_path(label)
    conf["snapshots_csv"] = snapshot_csv

    if Path(snapshot_csv).exists() and not overwrite:
        log_info(f"📄 Using existing snapshots: {snapshot_csv}")
        return snapshot_csv

    start = conf.get("start_date", "2023-01-01")
    end = conf.get("end_date", "2023-12-31")

    if dry_run:
        log_dryrun(f"Would generate snapshots for {label} → {snapshot_csv}")
        return snapshot_csv

    log_info(f"📦 Generating snapshots for: {label}")
    cmd = [
        PYTHON,
        SNAPSHOT_SCRIPT,
        "--input_dir",
        BETFAIR_DATA_DIR,
        "--output_csv",
        snapshot_csv,
        "--start_date",
        start,
        "--end_date",
        end,
        "--mode",
        "full",
        "--overwrite",
    ]
    t0 = time.perf_counter()
    try:
        subprocess.run(
            cmd,
            check=True,
            env={**os.environ, "PYTHONPATH": "."},
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        t1 = time.perf_counter()
        log_success(f"✅ Parsed snapshots to {snapshot_csv} in {t1 - t0:.2f}s")
    except subprocess.CalledProcessError as e:
        log_error(f"❌ Snapshot parsing failed for {label}: {e}")
        raise
    return snapshot_csv


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Build raw matches for all tournaments in YAML config."
    )
    parser.add_argument(
        "--config",
        default="configs/tournaments.yaml",
        help="Path to tournaments YAML config",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Top‐level dry-run notice
    if _args.dry_run:
        log_dryrun(f"Would build all tournaments from {_args.config}")

    # Validate config
    try:
        cfg = validate_yaml(_args.config, TOURNAMENTS_SCHEMA)
    except Exception as e:
        log_error(f"❌ Invalid YAML config {_args.config}: {e}")
        return

    defaults = cfg.get("defaults", {})
    tournaments = cfg.get("tournaments", [])

    for t in tournaments:
        conf = {**defaults, **t}
        label = conf.get("label")
        log_info(f"\n🏗️ Building: {label}")

        try:
            # Parse snapshots if needed
            snapshot_csv = parse_snapshots_if_needed(
                conf, _args.overwrite, _args.dry_run
            )

            paths = get_pipeline_paths(label)
            output_path = paths["raw_csv"]

            if not should_run(output_path, _args.overwrite, _args.dry_run):
                continue

            # Build clean matches
            cmd = [
                PYTHON,
                BUILDER_SCRIPT,
                "--tour",
                conf["tour"],
                "--tournament",
                conf["tournament"],
                "--year",
                str(conf["year"]),
                "--snapshots_csv",
                snapshot_csv,
                "--output_csv",
                str(output_path),
                "--overwrite",
            ]
            if conf.get("sackmann_csv") and not conf.get("snapshot_only", False):
                cmd += ["--sackmann_csv", conf["sackmann_csv"]]
            if conf.get("snapshot_only"):
                cmd.append("--snapshot_only")
            if conf.get("fuzzy_match"):
                cmd.append("--fuzzy_match")
            if "alias_csv" in conf:
                cmd += ["--alias_csv", conf["alias_csv"]]

            if _args.dry_run:
                log_dryrun(f"Would run: {' '.join(cmd)}")
                continue

            t0 = time.perf_counter()
            subprocess.run(
                cmd,
                check=True,
                env={**os.environ, "PYTHONPATH": "."},
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            t1 = time.perf_counter()
            log_success(f"✅ Finished building {label} in {t1 - t0:.2f}s")

        except Exception as e:
            log_error(f"⚠️ Skipping {label} due to error: {e}")


if __name__ == "__main__":
    main()
