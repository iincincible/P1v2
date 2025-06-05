import argparse
import subprocess
import yaml
from pathlib import Path
import sys
import time

PYTHON = sys.executable

def run_pipeline_for_tournament(tournament, skip_existing=False):
    key = tournament["key"]
    base = f"data/processed/{key}"
    parsed = f"parsed/betfair_{key}_snapshots.csv"

    print(f"\n🚀 Running pipeline for: {key}")

    preds_csv = f"{base}_predictions.csv"
    value_bets_csv = f"{base}_value_bets.csv"
    bankroll_csv = f"{base}_bankroll.csv"
    ev_threshold = str(tournament.get("ev_threshold", 0.01))

    if skip_existing and Path(preds_csv).exists():
        print(f"⏭️ Skipping {key} — predictions already exist at {preds_csv}")
        return True

    steps = [
        ("Match selection IDs", [
            PYTHON, "scripts/pipeline/match_selection_ids.py",
            "--merged_csv", f"{base}_clean_snapshot_matches.csv",
            "--snapshots_csv", parsed,
            "--output_csv", f"{base}_ids.csv"
        ]),
        ("Merge final LTPs", [
            PYTHON, "scripts/pipeline/merge_final_ltps_into_matches.py",
            "--match_csv", f"{base}_ids.csv",
            "--snapshots_csv", parsed,
            "--output_csv", f"{base}_with_odds.csv"
        ]),
        ("Build odds features", [
            PYTHON, "scripts/pipeline/build_odds_features.py",
            "--input_csv", f"{base}_with_odds.csv",
            "--output_csv", f"{base}_features.csv"
        ]),
        ("Predict win probabilities", [
            PYTHON, "scripts/pipeline/predict_win_probs.py",
            "--input_csv", f"{base}_features.csv",
            "--model_path", "modeling/win_model.pkl",
            "--output_csv", preds_csv
        ]),
        ("Detect value bets", [
            PYTHON, "scripts/pipeline/detect_value_bets.py",
            "--input_csv", preds_csv,
            "--output_csv", value_bets_csv,
            "--ev_threshold", ev_threshold,
            "--max_odds", "10.0",
            "--max_margin", "0.05",
            "--filter_model", "modeling/ev_filter_model.pkl",
            "--min_confidence", "0.5"
        ]),
        ("Simulate bankroll", [
            PYTHON, "scripts/pipeline/simulate_bankroll_growth.py",
            "--input_csvs", value_bets_csv,
            "--output_csv", bankroll_csv,
            "--strategy", "flat",
            "--ev_threshold", ev_threshold,
            "--odds_cap", "10.0"
        ])
    ]

    for step_name, cmd in steps:
        try:
            print(f"🔧 Step: {step_name}")
            t0 = time.perf_counter()
            subprocess.run(cmd, check=True)
            t1 = time.perf_counter()
            print(f"✅ {step_name} completed in {t1 - t0:.2f} seconds")
        except subprocess.CalledProcessError:
            print(f"❌ Pipeline failed for {key} during step: {step_name}")
            return False

    print(f"✅ {key}: pipeline complete — predictions, value bets, and bankroll simulated.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config with tournaments list")
    parser.add_argument("--skip_existing", action="store_true", help="Skip tournaments if predictions already exist")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    for tournament in config["tournaments"]:
        success = run_pipeline_for_tournament(tournament, skip_existing=args.skip_existing)
        if not success:
            print(f"⚠️ Aborting further processing due to error in {tournament['key']}")
            break
