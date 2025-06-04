import argparse
import subprocess
from pathlib import Path
import yaml

def run_pipeline(config):
    PYTHON = ".venv/Scripts/python.exe"

    label = config["label"]
    base = f"data/processed/{label}"
    snapshots_csv = config["snapshots_csv"]
    sackmann_csv = config.get("sackmann_csv")
    alias_csv = config.get("alias_csv")
    fuzzy = config.get("fuzzy_match", False)
    snapshot_only = config.get("snapshot_only", False)

    merged_csv = f"{base}_merged.csv"

    # Step 1: Build clean matches
    builder_cmd = [
        PYTHON, "scripts/builders/build_clean_matches_generic.py",
        "--tour", config["tour"],
        "--tournament", config["tournament"],
        "--year", str(config["year"]),
        "--snapshots_csv", snapshots_csv,
        "--output_csv", merged_csv
    ]
    if sackmann_csv and not snapshot_only:
        builder_cmd += ["--sackmann_csv", sackmann_csv]
    if snapshot_only:
        builder_cmd.append("--snapshot_only")
    if fuzzy:
        builder_cmd.append("--fuzzy_match")
    if alias_csv:
        builder_cmd += ["--alias_csv", alias_csv]

    subprocess.run(builder_cmd, check=True)

    # Step 2: Match selection IDs
    ids_csv = f"{base}_ids.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/match_selection_ids.py",
        "--merged_csv", merged_csv,
        "--snapshots_csv", snapshots_csv,
        "--output_csv", ids_csv
    ], check=True)

    # Step 3: Merge final LTPs
    patched_csv = f"{base}_with_odds.csv"
    subprocess.run([
        PYTHON, "scripts/builders/merge_final_ltps_into_matches.py",
        "--match_csv", ids_csv,
        "--snapshots_csv", snapshots_csv,
        "--output_csv", patched_csv
    ], check=True)

    # Step 4: Build odds features
    features_csv = f"{base}_features.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/build_odds_features.py",
        "--input_csv", patched_csv,
        "--output_csv", features_csv
    ], check=True)

    # Step 5: Train win model
    preds_csv = f"{base}_predictions.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/train_win_model_from_odds.py",
        "--input_csv", features_csv,
        "--output_csv", preds_csv
    ], check=True)

    # Step 6: Detect value bets
    value_csv = f"{base}_value_bets.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/detect_value_bets.py",
        "--input_csv", preds_csv,
        "--output_csv", value_csv
    ], check=True)

    # Step 7: Simulate bankroll growth
    bankroll_csv = f"modeling/{label}_bankroll.csv"
    subprocess.run([
        PYTHON, "scripts/pipeline/simulate_bankroll_growth.py",
        "--input_csvs", value_csv,
        "--output_csv", bankroll_csv,
        "--ev_threshold", "0.05",
        "--odds_cap", "10",
        "--plot"
    ], check=True)

    print(f"✅ Pipeline complete for {label}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="YAML config file for the tournament")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    run_pipeline(config)

if __name__ == "__main__":
    main()
