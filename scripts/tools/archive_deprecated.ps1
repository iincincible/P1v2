$archivedFolder = "C:\Users\lucap\Projects\P1v2\scripts\archive"

# Ensure the archive folder exists
if (-not (Test-Path $archivedFolder)) {
    New-Item -ItemType Directory -Path $archivedFolder | Out-Null
}

# List of deprecated builder scripts
$deprecatedScripts = @(
    "merge_ltps_by_ids.py",
    "merge_ltps_into_repaired_matches.py"
)

# Move each script to the archive folder
foreach ($script in $deprecatedScripts) {
    $source = "C:\Users\lucap\Projects\P1v2\scripts\builders\$script"
    $destination = Join-Path $archivedFolder $script
    if (Test-Path $source) {
        Move-Item $source $destination
        Write-Host "✅ Archived $script"
    } else {
        Write-Host "⚠️ Not found: $script"
    }
}
