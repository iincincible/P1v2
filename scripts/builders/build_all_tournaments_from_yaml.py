import yaml
import subprocess
from pathlib import Path
import sys
import os
import time

PYTHON = sys.executable
CONFIG_FILE = "configs/tournaments_2023.yaml"
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"
SNAPSHOT_SCRIPT = "scripts/pipeline/parse_betfair_snapshots.py"
BETFAIR_DATA_DIR = "data/BASIC"

TOURNAMENT_WINDOWS = {
    "australian_open": ("2023-01-15", "2023-01-30"),
    "roland_garros": ("2023-05-28", "2023-06-11"),
    "wimbledon": ("2023-07-03", "2023-07-16"),
    "us_open": ("2023-08-28", "2023-09-10"),
    "indian_wells": ("2023-03-06", "2023-03-19"),
    "miami": ("2023-03-20", "2023-04-02"),
    "madrid": ("2023-04-24", "2023-05-07"),
}

def parse_snapshots_if_missing(conf):
    label = conf["label"]
    snapshot_csv = f"parsed/betfair_{label}_snapshots.csv"

    if Path(snapshot_csv).exists():
        print(f"🟢 Snapshots already exist: {snapshot_csv}")
        return

    tourney = conf["tournament"]
    start, end = TOURNAMENT_WINDOWS.get(tourney, ("2023-01-01", "2023-12-31"))

    print(f"📦 Generating snapshots for: {label}")
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
        subprocess.run(cmd, check=True)
        t1 = time.perf_counter()
        print(f"✅ Parsed snapshots to {snapshot_csv} in {t1 - t0:.2f} seconds")
    except subprocess.CalledProcessError as e:
        print(f"❌ Snapshot parsing failed for {label}")
        print(f"    Command: {' '.join(cmd)}")
        print(f"    Error: {e}")
        raise

# === Main Tournament Loop ===
with open(CONFIG_FILE, "r") as f:
    configs = yaml.safe_load(f)

for conf in configs["tournaments"]:
    label = conf["label"]
    print(f"\n🏗️ Building: {label}")
    try:
        parse_snapshots_if_missing(conf)

        output_path = f"data/processed/{label}_clean_snapshot_matches.csv"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            PYTHON, BUILDER_SCRIPT,
            "--tour", conf["tour"],
            "--tournament", conf["tournament"],
            "--year", str(conf["year"]),
            "--snapshots_csv", conf["snapshots_csv"],
            "--output_csv", output_path
        ]

        if not conf.get("snapshot_only", False):
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
        print(f"✅ Finished: {label} in {t1 - t0:.2f} seconds")
    except Exception:
        print(f"⚠️ Skipping {label} due to error.")
