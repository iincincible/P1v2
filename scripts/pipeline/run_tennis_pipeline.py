import argparse
import subprocess
from pathlib import Path

def run_pipeline(tour, start_date, end_date, label):
    PYTHON = ".venv/Scripts/python.exe"

    # File paths
    base = f"data/processed/{label}"
    snapshots_csv = "parsed/betfair_tennis_snapshots.csv"
    match_csv = f"data/tennis_{tour.lower()}/{tour.lower()}_matches_2023.csv"
    merged_csv = f"{base}_merged.csv"
    ids_csv = f"{base}_ids.csv"
    patched_csv = f"{base}_patched.csv"
    features_csv = f"{base}_features.csv"
    preds_csv = f"{base}_predictions.csv"
    value_csv = f"{base}_value_bets.csv"
    sim_csv = f"modeling/{label}_bankroll.csv"
    player_roi_csv = f"modeling/{label}_player_roi.csv"
    matchup_roi_csv = f"modeling/{label}_matchup_roi.csv"
    bankroll_plot = f"data/plots/bankroll_curves/bankroll_{label}.png"

    subprocess.run([
        PYTHON, "scripts/parse_betfair_snapshots.py",
        "--input_dir", "data/BASIC/",
        "--output_csv", snapshots_csv,
        "--start_date", start_date,
        "--end_date", end_date,
        "--mode", "full"
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/merge_sackmann_with_snapshots.py",
        "--match_csv", match_csv,
        "--snapshots_csv", snapshots_csv,
        "--ltps_csv", snapshots_csv,
        "--output_csv", merged_csv
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/match_selection_ids.py",
        "--merged_csv", merged_csv,
        "--snapshots_csv", snapshots_csv,
        "--output_csv", ids_csv,
        "--method", "jaro_winkler",
        "--fuzzy_threshold", "0.85"
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/merge_ltps_by_ids.py",
        "--merged_csv", ids_csv,
        "--ltps_csv", snapshots_csv,
        "--output_csv", patched_csv
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/build_odds_features.py",
        "--input_csv", patched_csv,
        "--output_csv", features_csv,
        "--cap", "10.0"
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/train_win_model_from_odds.py",
        "--input_csv", features_csv,
        "--output_csv", preds_csv
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/detect_value_bets.py",
        "--input_csv", preds_csv,
        "--output_csv", value_csv
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/simulate_bankroll_growth.py",
        "--input_glob", value_csv,
        "--output_csv", sim_csv,
        "--ev_threshold", "0.05",
        "--odds_cap", "10",
        "--plot",
        "--plot_path", bankroll_plot
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/log_player_matchup_roi.py",
        "--input_glob", sim_csv,
        "--player_output_csv", player_roi_csv,
        "--matchup_output_csv", matchup_roi_csv
    ], check=True)

    subprocess.run([
        PYTHON, "scripts/combine_bankrolls.py"
    ], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tour", required=True, choices=["ATP", "WTA"])
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    run_pipeline(args.tour, args.start_date, args.end_date, args.label)

if __name__ == "__main__":
    main()
