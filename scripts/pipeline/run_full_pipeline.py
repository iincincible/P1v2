import argparse
import yaml
import subprocess
import time
import os
from pathlib import Path
from scripts.utils.paths import get_pipeline_paths, DEFAULT_MODEL_PATH
from scripts.utils.logger import log_info, log_success, log_warning, log_error

PYTHON = os.environ.get("PYTHON", "python")
SELECTION_SCRIPT = "scripts/pipeline/match_selection_ids.py"
MERGE_SCRIPT = "scripts/pipeline/merge_final_ltps_into_matches.py"
FEATURE_SCRIPT = "scripts/pipeline/build_odds_features.py"
PREDICT_SCRIPT = "scripts/pipeline/predict_win_probs.py"
VALUE_SCRIPT = "scripts/pipeline/detect_value_bets.py"
SIM_SCRIPT = "scripts/pipeline/simulate_bankroll.py"

def run(cmd, label=None):
    try:
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
    except subprocess.CalledProcessError as e:
        step = cmd[-2] if len(cmd) >= 2 else str(cmd)
        log_error(f"Pipeline failed{f' for {label}' if label else ''} during step: {step}")
        raise

def run_pipeline(tournament, skip_existing):
    label = tournament["label"]
    paths = get_pipeline_paths(label)
    model_path = tournament.get("model_path", DEFAULT_MODEL_PATH)

    log_info(f"Running pipeline for: {label}")

    steps = [
        ("Match selection IDs", SELECTION_SCRIPT, [
            "--merged_csv", str(paths["raw_csv"]),
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", str(paths["ids_csv"])
        ], paths["ids_csv"]),

        ("Merge final LTPs", MERGE_SCRIPT, [
            "--match_csv", str(paths["ids_csv"]),
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", str(paths["odds_csv"])
        ], paths["odds_csv"]),

        ("Build odds features", FEATURE_SCRIPT, [
            "--input_csv", str(paths["odds_csv"]),
            "--output_csv", str(paths["features_csv"])
        ], paths["features_csv"]),

        ("Predict win probabilities", PREDICT_SCRIPT, [
            "--input_csv", str(paths["features_csv"]),
            "--model_path", model_path,
            "--output_csv", str(paths["predictions_csv"])
        ], paths["predictions_csv"]),

        ("Detect value bets", VALUE_SCRIPT, [
            "--input_csv", str(paths["predictions_csv"]),
            "--output_csv", str(paths["value_csv"])
        ], paths["value_csv"]),

        ("Simulate bankroll", SIM_SCRIPT, [
            "--input_csvs", str(paths["value_csv"]),
            "--output_csv", str(paths["bankroll_csv"]),
            "--strategy", "kelly",
            "--ev_threshold", "0.2",
            "--odds_cap", "6.0",
            "--plot"
        ], paths["bankroll_csv"]),
    ]

    for step_name, script, cmd_args, output_path in steps:
        log_info(f"🔧 Step: {step_name}")
        if not skip_existing or not Path(output_path).exists():
            run([PYTHON, script] + cmd_args, label)
        else:
            log_info(f"⏭️ Skipping {output_path} (already exists)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--skip_existing", action="store_true")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    for tournament in config["tournaments"]:
        try:
            run_pipeline(tournament, args.skip_existing)
        except Exception:
            log_error(f"Aborting further processing due to error in {tournament['label']}")
            break

if __name__ == "__main__":
    main()
