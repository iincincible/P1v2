# clean_large_files_bfg.ps1

# Exit on error
$ErrorActionPreference = "Stop"

# Set variables
$repoPath = "$PSScriptRoot\..\..\.."  # adjust to repo root from /scripts/tools
$largeFilePath = "parsed/betfair_ausopen_2023_atp_snapshots.csv"
$bfgJar = "$PSScriptRoot\bfg.jar"

# Navigate to repo root
Set-Location -Path $repoPath

# Make backup just in case
if (-not (Test-Path "$repoPath\repo-backup")) {
    git clone --mirror . .\repo-backup
}

# Run BFG to remove the large file from history
java -jar $bfgJar --delete-files $largeFilePath

# Cleanup and finalize
git reflog expire --expire=now --all
git gc --prune=now --aggressive
