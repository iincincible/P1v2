import zipfile
from pathlib import Path

output_zip = Path("frenchopen_2023_core_outputs.zip")
files = [
    "data/processed/merged_frenchopen_2023.csv",
    "data/processed/merged_frenchopen_2023_patched.csv",
    "data/processed/match_level_training_frenchopen_2023.csv",
    "data/processed/expanded_training_frenchopen_2023_v3.csv",
    "data/processed/expanded_training_frenchopen_2023_v3_patched.csv",
    "data/processed/predictions_frenchopen_2023.csv",
    "data/processed/value_bets_frenchopen_2023.csv",
    "data/processed/bankroll_sim_frenchopen_2023.csv",
    "data/processed/player_roi_frenchopen_2023.csv",
    "data/processed/matchup_roi_frenchopen_2023.csv"
]

with zipfile.ZipFile(output_zip, 'w') as zipf:
    for file in files:
        path = Path(file)
        if path.exists():
            zipf.write(path, arcname=path.name)
            print(f"✅ Added: {file}")
        else:
            print(f"⚠️ Missing: {file}")

print(f"\n📦 Created: {output_zip}")
