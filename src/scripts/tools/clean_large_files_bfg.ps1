# clean_large_files_bfg.ps1

$ErrorActionPreference = "Stop"

# Go to repo root
$repoRoot = "C:\Users\lucap\Projects\P1v2"
Set-Location -Path $repoRoot

# Backup (optional, for safety)
if (-not (Test-Path "$repoRoot\repo-backup")) {
    git clone --mirror . .\repo-backup
}

# Run BFG to delete the large file by filename only (not path)
java -jar "$PSScriptRoot\bfg.jar" --delete-files betfair_ausopen_2023_atp_snapshots.csv

# Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive
