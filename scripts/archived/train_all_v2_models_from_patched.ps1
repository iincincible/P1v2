# File: scripts/train_all_v2_models_from_patched.ps1

$files = Get-ChildItem "data/processed/merged_*_2023_deduped_patched.csv"

foreach ($file in $files) {
    $inputPath = $file.FullName
    $outputPath = $inputPath -replace "merged_", "predictions_" `
                              -replace "_patched.csv", ".csv"

    Write-Host "🤖 Training v2 model on $($file.Name)"
    .venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
        --input_csv "$inputPath" `
        --output_csv "$outputPath" `
        --preserve_winner_name
}
