import argparse
import yaml
import subprocess
import time
import os
from pathlib import Path
from scripts.utils.paths import get_pipeline_paths, DEFAULT_MODEL_PATH
from scripts.utils.logger import log_info, log_success, log_warning, log_error

PYTHON = str(Path(".venv/Scripts/python.exe").resolve()) if Path(".venv/Scripts/python.exe").exists() else "python"

SELECTION_SCRIPT = "scripts/pipeline/match_selection_ids.py"
MERGE_SCRIPT = "scripts/pipeline/merge_final_ltps_into_matches.py"
FEATURE_SCRIPT = "scripts/pipeline/build_odds_features.py"
PREDICT_SCRIPT = "scripts/pipeline/predict_win_probs.py"
VALUE_SCRIPT = "scripts/pipeline/detect_value_bets.py"
SIM_SCRIPT = "scripts/pipeline/simulate_bankroll_growth.py"

def run(cmd, label=None):
    try:
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
    except subprocess.CalledProcessError as e:
        step = cmd[-2] if len(cmd) >= 2 else str(cmd)
        log_error(f"Pipeline failed{f' for {label}' if label else ''} during step: {step}")
        raise

def run_step_if_needed(step_name, script, args_list, output_path, label, skip_existing):
    log_info(f"🔧 Step: {step_name}")
    if not skip_existing or not Path(output_path).exists():
        run([PYTHON, script] + args_list, label)
    else:
        log_info(f"⏭️ Skipping {output_path} (already exists)")

def run_pipeline(tournament, skip_existing, dry_run):
    label = tournament["label"]
    paths = get_pipeline_paths(label)
    model_path = tournament.get("model_path", DEFAULT_MODEL_PATH)

    log_info(f"📦 Starting pipeline for: {label}")

    # === Validate required input files ===
    required_inputs = {
        "snapshots_csv": tournament["snapshots_csv"],
        "raw_csv": paths["raw_csv"],
        "model_path": model_path,
    }

    for key, path in required_inputs.items():
        if not Path(path).exists():
            log_error(f"❌ Missing {key}: {path}")
            raise FileNotFoundError(f"{key} does not exist: {path}")

    steps = [
        ("Match selection IDs", SELECTION_SCRIPT, [
            "--merged_csv", str(paths["raw_csv"]),
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", str(paths["ids_csv"]),
            "--overwrite"
        ], paths["ids_csv"]),

        ("Merge final LTPs", MERGE_SCRIPT, [
            "--match_csv", str(paths["ids_csv"]),
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", str(paths["odds_csv"]),
            "--overwrite"
        ], paths["odds_csv"]),

        ("Build odds features", FEATURE_SCRIPT, [
            "--input_csv", str(paths["odds_csv"]),
            "--output_csv", str(paths["features_csv"]),
            "--overwrite"
        ], paths["features_csv"]),

        ("Predict win probabilities", PREDICT_SCRIPT, [
            "--input_csv", str(paths["features_csv"]),
            "--model_path", model_path,
            "--output_csv", str(paths["predictions_csv"]),
            "--overwrite"
        ], paths["predictions_csv"]),

        ("Detect value bets", VALUE_SCRIPT, [
            "--input_csv", str(paths["predictions_csv"]),
            "--output_csv", str(paths["value_csv"]),
            "--overwrite"
        ], paths["value_csv"]),

        ("Simulate bankroll", SIM_SCRIPT, [
            "--input_csvs", str(paths["value_csv"]),
            "--output_csv", str(paths["bankroll_csv"]),
            "--strategy", "kelly",
            "--ev_threshold", "0.2",
            "--odds_cap", "6.0",
            "--plot",
            "--overwrite"
        ], paths["bankroll_csv"]),
    ]

    if dry_run:
        for _, _, cmd_args, _ in steps:
            cmd_args.append("--dry_run")

    for step_name, script, cmd_args, output_path in steps:
        run_step_if_needed(step_name, script, cmd_args, output_path, label, skip_existing)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--skip_existing", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    defaults = config.get("defaults", {})

    for tournament in config["tournaments"]:
        tournament = {**defaults, **tournament}
        try:
            run_pipeline(tournament, args.skip_existing, args.dry_run)
        except Exception:
            log_error(f"🛑 Aborting further processing due to error in {tournament['label']}")
            break

if __name__ == "__main__":
    main()
