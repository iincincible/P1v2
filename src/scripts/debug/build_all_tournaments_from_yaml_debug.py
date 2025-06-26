import yaml
import sys

# Replace with your pipeline label if running standalone, or get from args
pipeline_label = "ausopen_2023_atp"

# Load YAML config
with open("configs/tournaments_2023_atp_ausopen.yaml") as f:
    yml = yaml.safe_load(f)

print("Loaded top-level YAML keys:", yml.keys())

# List all tournaments
tournaments = yml.get("tournaments", [])
print(f"Found {len(tournaments)} tournaments in config.")

# Print all available tournament labels
print("Available tournament labels in config:")
for t in tournaments:
    print(
        "-",
        t.get("label"),
        "| year:",
        t.get("year"),
        "| tournament:",
        t.get("tournament"),
    )

# Select tournament by label
selected = [t for t in tournaments if t.get("label") == pipeline_label]
if not selected:
    print(f"ERROR: No tournament entry with label '{pipeline_label}' found!")
    sys.exit(1)
tournament = selected[0]

print("\n--- Selected tournament dict ---")
print(tournament)

# Check required keys
for k in ["tournament", "year", "label"]:
    if k not in tournament:
        print(f"ERROR: Key '{k}' missing from tournament dict: {tournament}")
        sys.exit(1)
print("All required keys are present in selected tournament.")

# (Simulate) Call the builder function, passing the dict
print("\nWould call builder with:")
print(f"  tournament: {tournament['tournament']}")
print(f"  year: {tournament['year']}")
print(f"  label: {tournament['label']}")
print(f"  snapshots_csv: {tournament.get('snapshots_csv')}")

# This is where the original script would do the building
print("\n(Script completed without KeyError)")
