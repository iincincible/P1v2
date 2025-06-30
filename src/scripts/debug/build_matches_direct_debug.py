import sys

import yaml

# Import your build_matches function
sys.path.append("src/scripts/builders")
from build_clean_matches_generic import build_matches

# Read your YAML
with open("configs/tournaments_2023_atp_ausopen.yaml") as f:
    yml = yaml.safe_load(f)
tournament = yml["tournaments"][0]

# Show what you got from the config
print("\n=== TOURNAMENT ENTRY ===")
for k, v in tournament.items():
    print(f"{k}: {v}")

# Call the builder with debug prints enabled
try:
    build_matches(
        tour=tournament["tour"],
        tournament=tournament["tournament"],
        year=tournament["year"],
        snapshots_csv=tournament["snapshots_csv"],
        output_csv="debug_ausopen_2023_matches.csv",
        sackmann_csv=yml["defaults"].get("sackmann_csv"),
        alias_csv=yml["defaults"].get("alias_csv"),
        snapshot_only=yml["defaults"].get("snapshot_only", False),
        fuzzy_match=yml["defaults"].get("fuzzy_match", False),
        overwrite=True,
        dry_run=False,
    )
except Exception as e:
    print("\n❌ Exception during build_matches:", e)
