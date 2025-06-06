import argparse
import yaml
import subprocess
import os
from pathlib import Path

# ✅ Ensure the subprocesses use .venv explicitly
PYTHON = os.environ.get("PYTHON", str(Path(".venv/Scripts/python.exe").resolve()))

# Paths to individual step scripts
SELECTION_SCRIPT = "scripts/pipeline/match_selection_ids.py"
MERGE_SCRIPT = "scripts/pipeline/merge_final_ltps_into_matches.py"
FEATURE_SCRIPT = "scripts/pipeline/build_odds_features.py"
PREDICT_SCRIPT = "scripts/pipeline/predict_win_probs.py"
VALUE_SCRIPT = "scripts/pipeline/detect_value_bets.py"
SIM_SCRIPT = "scripts/pipeline/simulate_bankroll.py"

def run(cmd):
    subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})

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

    # Step 1: Match selection IDs
    print("🔧 Step: Match selection IDs")
    if not skip_existing or not Path(paths["ids_csv"]).exists():
        cmd = [
            PYTHON, SELECTION_SCRIPT,
            "--input_csv", paths["raw_csv"],
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", paths["ids_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['ids_csv']} (already exists)")

    # Step 2: Merge final LTPs
    print("🔧 Step: Merge final LTPs")
    if not skip_existing or not Path(paths["odds_csv"]).exists():
        cmd = [
            PYTHON, MERGE_SCRIPT,
            "--merged_csv", paths["ids_csv"],
            "--snapshots_csv", tournament["snapshots_csv"],
            "--output_csv", paths["odds_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['odds_csv']} (already exists)")

    # Step 3: Build odds features
    print("🔧 Step: Build odds features")
    if not skip_existing or not Path(paths["features_csv"]).exists():
        cmd = [
            PYTHON, FEATURE_SCRIPT,
            "--input_csv", paths["odds_csv"],
            "--output_csv", paths["features_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['features_csv']} (already exists)")

    # Step 4: Predict win probabilities
    print("🔧 Step: Predict win probabilities")
    if not skip_existing or not Path(paths["predictions_csv"]).exists():
        cmd = [
            PYTHON, PREDICT_SCRIPT,
            "--input_csv", paths["features_csv"],
            "--model_path", "modeling/final_model.joblib",
            "--output_csv", paths["predictions_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['predictions_csv']} (already exists)")

    # Step 5: Detect value bets
    print("🔧 Step: Detect value bets")
    if not skip_existing or not Path(paths["value_csv"]).exists():
        cmd = [
            PYTHON, VALUE_SCRIPT,
            "--predictions_csv", paths["predictions_csv"],
            "--output_csv", paths["value_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['value_csv']} (already exists)")

    # Step 6: Simulate bankroll
    print("🔧 Step: Simulate bankroll")
    if not skip_existing or not Path(paths["bankroll_csv"]).exists():
        cmd = [
            PYTHON, SIM_SCRIPT,
            "--value_bets_csv", paths["value_csv"],
            "--output_csv", paths["bankroll_csv"]
        ]
        run(cmd)
    else:
        print(f"⏭️ Skipping {paths['bankroll_csv']} (already exists)")

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
        except subprocess.CalledProcessError as e:
            print(f"❌ Pipeline failed for {tournament['label']} during step: {e.cmd[-2]}")
            print(f"⚠️ Aborting further processing due to error in {tournament['label']}")
            break

if __name__ == "__main__":
    main()
