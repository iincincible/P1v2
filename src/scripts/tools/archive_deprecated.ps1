# archive_deprecated.ps1
$DeprecatedFiles = @(
    "scripts\builders\extract_valid_ausopen_market_ids.py",
    "scripts\builders\extract_sackmann_matches.py",
    "scripts\builders\group_markets_by_day.py",
    "scripts\builders\extract_market_ids.py",
    "scripts\builders\filter_snapshots.py",
    "scripts\pipeline\expand_and_balance_dataset.py",
    "scripts\analysis\compare_ev_bins.py",
    "scripts\utils\merge_csvs_no_dup_header.py",
    "scripts\builders\match_snapshots_to_results.py"
)

$ArchiveFolder = "scripts\archive"

foreach ($file in $DeprecatedFiles) {
    $dest = Join-Path -Path $ArchiveFolder -ChildPath (Split-Path $file -Leaf)
    if (Test-Path $file) {
        Move-Item $file $dest -Force
        Write-Host "✅ Archived: $file -> $dest"
    } else {
        Write-Host "⚠️ File not found: $file"
    }
}
