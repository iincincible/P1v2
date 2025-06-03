# Loop over all filtered merged datasets and retrain the win model with true labels (won column)

$files = Get-ChildItem -Path "data/processed" -Filter "merged_*_2023_deduped_filtered.csv"

foreach ($file in $files) {
    $inputCsv = $file.FullName
    $name = $file.BaseName.Replace("merged_", "").Replace("_deduped_filtered", "")
    $outputCsv = "data/processed/predictions_${name}_deduped.csv"

    Write-Host "🤖 Training v2 model on $($file.Name)"
    .venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
        --input_csv "$inputCsv" `
        --output_csv "$outputCsv" `
        --preserve_winner_name
}
