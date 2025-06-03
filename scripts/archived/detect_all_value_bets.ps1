# File: scripts/detect_all_value_bets.ps1

$files = Get-ChildItem "data/processed/predictions_*_2023_deduped.csv"

foreach ($file in $files) {
    $inputPath = $file.FullName
    $outputPath = $inputPath -replace "predictions_", "value_bets_"

    Write-Host "💸 Detecting value bets in $($file.Name)"
    .venv\Scripts\python.exe scripts/detect_value_bets.py `
        --input_csv "$inputPath" `
        --output_csv "$outputPath"
}
