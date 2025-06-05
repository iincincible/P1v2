import yaml
import subprocess
from pathlib import Path

# Path to your Python virtual environment interpreter
PYTHON = ".venv\\Scripts\\python.exe"
CONFIG_FILE = "configs/tournaments_2023.yaml"
BUILDER_SCRIPT = "scripts/builders/build_clean_matches_generic.py"

# Load YAML config
with open(CONFIG_FILE, "r") as f:
    configs = yaml.safe_load(f)

# Loop through each tournament config
for conf in configs["tournaments"]:
    print(f"\n🏗️ Building: {conf['label']}")

    cmd = [
        PYTHON, BUILDER_SCRIPT,
        "--tour", conf["tour"],
        "--tournament", conf["tournament"],
        "--year", str(conf["year"]),
        "--snapshots_csv", conf["snapshots_csv"],
        "--output_csv", f"data/processed/{conf['label']}_clean_snapshot_matches.csv"
    ]

    # Optional fields
    if not conf.get("snapshot_only", False):
        cmd += ["--sackmann_csv", conf["sackmann_csv"]]
    if conf.get("snapshot_only"):
        cmd.append("--snapshot_only")
    if conf.get("fuzzy_match"):
        cmd.append("--fuzzy_match")
    if "alias_csv" in conf:
        cmd += ["--alias_csv", conf["alias_csv"]]

    # Ensure output folder exists
    Path(f"data/processed/{conf['label']}_clean_snapshot_matches.csv").parent.mkdir(parents=True, exist_ok=True)

    # Run subprocess
    subprocess.run(cmd, check=True)
