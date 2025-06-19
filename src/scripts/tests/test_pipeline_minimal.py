import subprocess
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        sys.exit(1)

def test_pipeline():
    # Run full pipeline for AusOpen 2023 ATP from config
    run_cmd("python scripts/pipeline/run_full_pipeline.py --config configs/tournaments_2023.yaml --skip_existing")

    # Check some output files exist (adjust paths if needed)
    import os
    required_files = [
        "data/processed/ausopen_2023_atp_clean_snapshot_matches.csv",
        "data/processed/ausopen_2023_atp_ids.csv",
        "data/processed/ausopen_2023_atp_with_odds.csv",
        "data/processed/ausopen_2023_atp_features.csv",
        "data/processed/ausopen_2023_atp_predictions.csv",
        "data/processed/ausopen_2023_atp_value_bets.csv",
        "data/processed/ausopen_2023_atp_bankroll.csv",
    ]
    for f in required_files:
        if not os.path.exists(f):
            print(f"❌ Missing expected output: {f}")
            sys.exit(1)
        else:
            print(f"✅ Found output file: {f}")

if __name__ == "__main__":
    test_pipeline()
    print("🎉 Pipeline minimal test completed successfully.")
