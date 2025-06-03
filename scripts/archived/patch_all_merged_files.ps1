# File: scripts/patch_all_merged_files.ps1

$files = Get-ChildItem "data/processed/merged_*_2023_deduped.csv"

foreach ($file in $files) {
    $inputPath = $file.FullName
    $df = Import-Csv $inputPath

    # Load with pandas in Python to apply logic and save
    $outputPath = $inputPath -replace "_deduped.csv", "_deduped_patched.csv"

    Write-Host "🩹 Patching $($file.Name)"
    .venv\Scripts\python.exe scripts/patch_add_margin_diff.py `
        --input_csv "$inputPath" `
        --output_csv "$outputPath"
}
