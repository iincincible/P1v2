# Create archive folder if it doesn't exist
$archiveDir = "scripts/archive"
if (!(Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir
}

# Move deprecated or redundant scripts into archive
$toArchive = @(
    "fuzzy_repair_selection_ids.py",
    "merge_sackmann_with_snapshots.py",
    "merge_snapshots_and_results.py",
    "manual_value_bet_detector.py",
    "build_clean_matches_temp.py",
    "merge_snapshots_temp.py",
    "deprecated_train_model.py",
    "debug_ev_bins_old.py",
    "scan_snapshot_files_temp.py"
)

foreach ($script in $toArchive) {
    $sourcePath = "scripts/$script"
    $destinationPath = "$archiveDir/$script"
    if (Test-Path $sourcePath) {
        Move-Item $sourcePath $destinationPath -Force
        Write-Host "Moved $script to archive/"
    } else {
        Write-Host "$script not found, skipping."
    }
}
