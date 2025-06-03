# File: scripts/train_all_v2_models.ps1

$files = Get-ChildItem "data/processed/merged_*_2023_deduped.csv"

foreach ($file in $files) {
    $inputPath = $file.FullName
    $outputPath = $inputPath -replace "merged_", "predictions_"

    Write-Host "🔧 Training on $($file.Name)"
    .venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
        --input_csv "$inputPath" `
        --output_csv "$outputPath" `
        --preserve_winner_name
}
