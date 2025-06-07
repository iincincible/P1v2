import yaml
import subprocess
from pathlib import Path
import sys
import time
import os

from scripts.utils.paths import get_pipeline_paths, get_snapshot_csv_path
from scripts.utils.cli_utils import assert_file_exists
from scripts.utils.logger import log_info, log_success, log_warning, log_error

PYTHON = sys.executable
CONFIG_FILE = "configs/tournaments_2024.yaml"
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"
SNAPSHOT_SCRIPT = "scripts/pipeline/parse_betfair_snapshots.py"
BETFAIR_DATA_DIR = "data/BASIC"

def parse_snapshots_if_missing(conf):
    label = conf["label"]
    snapshot_csv = conf.get("snapshots_csv") or get_snapshot_csv_path(label)
    conf["snapshots_csv"] = snapshot_csv  # patch in case it was missing
    start = conf.get("start_date", "2023-01-01")
    end = conf.get("end_date", "2023-12-31")

    if Path(snapshot_csv).exists():
        log_info(f"🟢 Snapshots already exist: {snapshot_csv}")
        return

    log_info(f"📦 Generating snapshots for: {label}")
    cmd = [
        PYTHON, SNAPSHOT_SCRIPT,
        "--input_dir", BETFAIR_DATA_DIR,
        "--output_csv", snapshot_csv,
        "--start_date", start,
        "--end_date", end,
        "--mode", "full"
    ]

    try:
        t0 = time.perf_counter()
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
        t1 = time.perf_counter()
        log_success(f"✅ Parsed snapshots to {snapshot_csv} in {t1 - t0:.2f} seconds")
    except subprocess.CalledProcessError as e:
        log_error(f"❌ Snapshot parsing failed for {label}")
        log_error(f"    Command: {' '.join(cmd)}")
        log_error(f"    Error: {e}")
        raise

# === Main Tournament Loop ===
with open(CONFIG_FILE, "r") as f:
    configs = yaml.safe_load(f)

for conf in configs["tournaments"]:
    label = conf["label"]
    log_info(f"\n🏗️ Building: {label}")
    try:
        parse_snapshots_if_missing(conf)

        # Validate required files
        assert_file_exists(conf["snapshots_csv"], "snapshots_csv")
        if conf.get("sackmann_csv") and not conf.get("snapshot_only", False):
            assert_file_exists(conf["sackmann_csv"], "sackmann_csv")
        if "alias_csv" in conf:
            assert_file_exists(conf["alias_csv"], "alias_csv")

        output_path = get_pipeline_paths(label)["raw_csv"]
        if Path(output_path).exists():
            log_info(f"⏭️ Output already exists: {output_path}")
            continue

        cmd = [
            PYTHON, BUILDER_SCRIPT,
            "--tour", conf["tour"],
            "--tournament", conf["tournament"],
            "--year", str(conf["year"]),
            "--snapshots_csv", conf["snapshots_csv"],
            "--output_csv", str(output_path)
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
        log_error(f"⚠️ Skipping {label} due to error.")
        log_error(f"   {e}")
