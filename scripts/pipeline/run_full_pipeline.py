import argparse
import yaml
import subprocess
import time
import os
from pathlib import Path

# Scripts to run per step
PYTHON = os.environ.get("PYTHON", "python")
SELECTION_SCRIPT = "scripts/pipeline/match_selection_ids.py"
MERGE_SCRIPT = "scripts/pipeline/merge_final_ltps_into_matches.py"
FEATURE_SCRIPT = "scripts/pipeline/build_odds_features.py"
PREDICT_SCRIPT = "scripts/pipeline/predict_win_probs.py"
VALUE_SCRIPT = "scripts/pipeline/detect_value_bets.py"
SIM_SCRIPT = "scripts/pipeline/simulate_bankroll.py"

MODEL_PATH = "modeling/win_model.pkl"  # fallback model path

def run(cmd, label=None):
    try:
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
    except subprocess.CalledProcessError as e:
        step = cmd[-2] if len(cmd) >= 2 else str(cmd)
        print(f"❌ Pipeline failed{f' for {label}' if label else ''} during step: {step}")
        raise

def run_pipeline(tournament, skip_existing):
    label = tournament["label"]
    print(f"\n🚀 Running pipeline for: {label}")

    paths = {
        "raw_csv": f"data/processed/{label}_clean_snapshot_matches.csv",
        "ids_csv": f"data/processed/{label}_ids.csv",
        "odds_csv": f"data/processed/{label}_with_odds.csv",
        "features_csv": f"data/processed/{label}_features.csv",
        "predictions_csv": f"data/processed/{label}_predictions.csv",
        "value_csv": f"data/processed/{label}_value_bets.csv",
        "bankroll_csv": f"data/processed/{label}_bankroll.csv",
    }

    model_path = tournament.get("model_path", MODEL_PATH)

    steps = [
        ("Match selection IDs", SELECTION_SCRIPT, [
            "--input_csv", paths["raw_csv"],
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", paths["ids_csv"]
        ], paths["ids_csv"]),

        ("Merge final LTPs", MERGE_SCRIPT, [
            "--merged_csv", paths["ids_csv"],
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", paths["odds_csv"]
        ], paths["odds_csv"]),

        ("Build odds features", FEATURE_SCRIPT, [
            "--input_csv", paths["odds_csv"],
            "--output_csv", paths["features_csv"]
        ], paths["features_csv"]),

        ("Predict win probabilities", PREDICT_SCRIPT, [
            "--input_csv", paths["features_csv"],
            "--model_path", model_path,
            "--output_csv", paths["predictions_csv"]
        ], paths["predictions_csv"]),

        ("Detect value bets", VALUE_SCRIPT, [
            "--predictions_csv", paths["predictions_csv"],
            "--output_csv", paths["value_csv"]
        ], paths["value_csv"]),

        ("Simulate bankroll", SIM_SCRIPT, [
            "--value_bets_csv", paths["value_csv"],
            "--output_csv", paths["bankroll_csv"]
        ], paths["bankroll_csv"]),
    ]

    for step_name, script, cmd_args, output_path in steps:
        print(f"🔧 Step: {step_name}")
        if not skip_existing or not Path(output_path).exists():
            run([PYTHON, script] + cmd_args, label)
        else:
            print(f"⏭️ Skipping {output_path} (already exists)")

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
            print(f"⚠️ Aborting further processing due to error in {tournament['label']}")
            break

if __name__ == "__main__":
    main()
