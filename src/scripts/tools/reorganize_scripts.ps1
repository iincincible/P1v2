# Create target folders
$targets = @("pipeline", "builders", "debug")
foreach ($dir in $targets) {
    $path = "scripts/$dir"
    if (!(Test-Path $path)) {
        New-Item -ItemType Directory -Path $path
    }
}

# === Move pipeline scripts ===
$pipeline = @(
    "build_odds_features.py",
    "detect_value_bets.py",
    "simulate_bankroll_growth.py",
    "train_win_model_from_odds.py",
    "train_eval_model_cross_slam.py",
    "match_selection_ids.py",
    "merge_ltps_by_ids.py",
    "merge_ltps_into_repaired_matches.py",
    "run_tennis_pipeline.py"
)
foreach ($file in $pipeline) {
    if (Test-Path "scripts/$file") {
        Move-Item "scripts/$file" "scripts/pipeline/$file" -Force
        Write-Host "Moved $file to pipeline/"
    }
}

# === Move builder scripts ===
$builders = Get-ChildItem scripts -Filter "build_clean_matches_*"
$builders += Get-ChildItem scripts -Filter "build_snapshot_only_*"
$builders += Get-ChildItem scripts -Filter "extract_*"
$builders += Get-ChildItem scripts -Filter "filter_snapshots*"
$builders += Get-ChildItem scripts -Filter "join_snapshot_matches_with_results*"
foreach ($file in $builders) {
    Move-Item $file.FullName "scripts/builders/$($file.Name)" -Force
    Write-Host "Moved $($file.Name) to builders/"
}

# === Move debug scripts ===
$debug = Get-ChildItem scripts -Filter "debug_*.py"
$debug += Get-ChildItem scripts -Filter "inspect_*.py"
foreach ($file in $debug) {
    Move-Item $file.FullName "scripts/debug/$($file.Name)" -Force
    Write-Host "Moved $($file.Name) to debug/"
}
