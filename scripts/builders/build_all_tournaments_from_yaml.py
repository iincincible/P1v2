import yaml
import subprocess
from pathlib import Path

CONFIG_FILE = "configs/tournaments_2023.yaml"
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"

with open(CONFIG_FILE, "r") as f:
    configs = yaml.safe_load(f)

for conf in configs:
    print(f"\n🏗️ Building: {conf['name']}")

    cmd = [
        "python", BUILDER_SCRIPT,
        "--tour", conf["tour"],
        "--tournament", conf["tournament"],
        "--year", str(conf["year"]),
        "--snapshots_csv", conf["snapshots_csv"],
        "--output_csv", conf["output_csv"],
    ]

    # Optional: include Sackmann join if not snapshot-only
    if not conf.get("snapshot_only", False):
        cmd += ["--sackmann_csv", conf["sackmann_csv"]]

    # Optional flags
    if conf.get("snapshot_only"):
        cmd.append("--snapshot_only")
    if conf.get("fuzzy_match"):
        cmd.append("--fuzzy_match")
    if "alias_csv" in conf:
        cmd += ["--alias_csv", conf["alias_csv"]]

    Path(conf["output_csv"]).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)
