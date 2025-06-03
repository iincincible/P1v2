$deprecatedScripts = @(
    "scripts/build_match_level_training_set.py",
    "scripts/build_match_level_training_set_with_ids_patched.py",
    "scripts/build_training_set_from_snapshots.py",
    "scripts/cleanup_large_files.py",
    "scripts/debug_check_columns.py",
    "scripts/debug_repatch_odds.py",
    "scripts/expand_match_level_rows.py",
    "scripts/expand_match_rows_for_training.py",
    "scripts/extract_final_ltps.py",
    "scripts/extract_snapshots_from_filelist.py",
    "scripts/fetch_historical_odds.py",
    "scripts/filter_ausopen_matches.py",
    "scripts/filter_latest_snapshot_per_match.py",
    "scripts/filter_to_snapshot_markets.py",
    "scripts/fuzzy_repair_selection_ids.py",
    "scripts/merge_odds_with_results.py",
    "scripts/parse_betfair_tennis.py",
    "scripts/patch_add_margin_diff.py",
    "scripts/patch_cap_odds.py",
    "scripts/patch_fallback_odds_from_ltps.py",
    "scripts/patch_merge_with_ltps.py",
    "scripts/repair_selection_ids.py",
    "scripts/repatch_merge_with_ltps.py",
    "scripts/run_pipeline_frenchopen_2023_wta.py"
)

$archivePath = "scripts/archived"
if (-not (Test-Path $archivePath)) {
    New-Item -ItemType Directory -Path $archivePath
}

foreach ($script in $deprecatedScripts) {
    if (Test-Path $script) {
        Move-Item $script -Destination $archivePath
        Write-Host "📦 Archived $script to $archivePath"
    } else {
        Write-Host "⚠️ Not found: $script"
    }
}
Write-Host "✅ Archive complete."
