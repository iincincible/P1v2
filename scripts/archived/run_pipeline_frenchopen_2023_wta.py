import subprocess

def run_pipeline():
    steps = [
        ["python", "scripts/patch_merge_with_ltps.py",
            "--merge_csv", "data/processed/merged_frenchopen_2023_wta.csv",
            "--ltps_csv", "parsed/betfair_tennis_snapshots.csv",
            "--output_csv", "data/processed/merged_frenchopen_2023_wta_patched.csv"
        ],
        ["python", "scripts/patch_add_margin_diff.py", "--tournament", "frenchopen_2023", "--gender", "wta"],
        ["python", "scripts/patch_cap_odds.py", "--tournament", "frenchopen_2023", "--gender", "wta"],
        ["python", "scripts/train_win_model_from_odds.py", "--tournament", "frenchopen_2023", "--gender", "wta"],
        ["python", "scripts/detect_value_bets.py", "--tournament", "frenchopen_2023", "--gender", "wta"],
        ["python", "scripts/simulate_bankroll_growth.py",
            "--input_csvs", "data/processed/value_bets_frenchopen_2023_wta.csv",
            "--output_csv", "data/plots/bankroll_curves/frenchopen_2023_bankroll_wta.csv",
            "--plot",
            "--plot_path", "data/plots/bankroll_curves/frenchopen_2023_bankroll_wta.png",
            "--ev_threshold", "0.01",
            "--odds_cap", "10"
        ],
        ["python", "scripts/auto_push_outputs.py"]
    ]

    for step in steps:
        print(f"▶️ Running: {' '.join(step)}")
        subprocess.run(step, check=True)

if __name__ == "__main__":
    run_pipeline()
