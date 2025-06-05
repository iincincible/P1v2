import argparse
import subprocess
import yaml
import os

PYTHON = "python"

def run_pipeline_for_tournament(tournament):
    key = tournament["key"]  # e.g. indianwells_2023_atp
    base = f"data/processed/{key}"
    parsed = f"parsed/betfair_{key}_snapshots.csv"

    print(f"\n🚀 Running pipeline for: {key}")

    # Step 1: Match selection IDs
    subprocess.run([
        PYTHON, "scripts/pipeline/match_selection_ids.py",
        "--merged_csv", f"{base}_clean_snapshot_matches.csv",
        "--snapshots_csv", parsed,
        "--output_csv", f"{base}_ids.csv"
    ], check=True)

    # Step 2: Merge final LTPs
    subprocess.run([
        PYTHON, "scripts/pipeline/merge_final_ltps_into_matches.py",
        "--match_csv", f"{base}_ids.csv",
        "--snapshots_csv", parsed,
        "--output_csv", f"{base}_with_odds.csv"
    ], check=True)

    # Step 3: Build odds features
    features_csv = f"{base}_features.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/build_odds_features.py",
        "--input_csv", f"{base}_with_odds.csv",
        "--output_csv", features_csv
    ], check=True)

    # Step 4: Predict win probabilities using pretrained model
    preds_csv = f"{base}_predictions.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/predict_win_probs.py",
        "--input_csv", features_csv,
        "--model_path", "modeling/win_model.pkl",
        "--output_csv", preds_csv
    ], check=True)

    # Step 5: Detect value bets
    subprocess.run([
        PYTHON, "scripts/pipeline/detect_value_bets.py",
        "--input_csv", preds_csv,
        "--output_csv", f"{base}_value_bets.csv",
        "--ev_threshold", "0.01",
        "--max_odds", "10.0",
        "--max_margin", "0.05",
        "--filter_model", "modeling/ev_filter_model.pkl",
        "--min_confidence", "0.5"
    ], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config with tournaments list")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    for tournament in config["tournaments"]:
        run_pipeline_for_tournament(tournament)
