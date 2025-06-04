#!/usr/bin/env python3
import subprocess

# Files to untrack due to GitHub file size limits
large_files = [
    "data/processed/merged_frenchopen_2023_wta_patched.csv",
    "data/processed/value_bets_frenchopen_2023_wta.csv",
    "data/processed/merged_frenchopen_2023_patched.csv",
    "data/processed/predictions_frenchopen_2023_wta.csv"
]

for file in large_files:
    try:
        subprocess.run(["git", "rm", "--cached", file], check=True)
        print(f"✅ Untracked: {file}")
    except subprocess.CalledProcessError:
        print(f"⚠️ Already untracked or missing: {file}")

# Final commit reminder
print("\nNext, run:")
print("git commit -m 'Remove large files that exceed GitHub limit'")
print("git push")
