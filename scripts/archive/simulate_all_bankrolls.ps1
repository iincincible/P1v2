# scripts/simulate_all_bankrolls.ps1

$files = Get-ChildItem -Path "data/processed" -Filter "value_bets_*_2023_deduped.csv"

foreach ($file in $files) {
    $inputPath = $file.FullName
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name).Replace("value_bets_", "")
    $outputCsv = "data/processed/bankroll_sim_${baseName}.csv"
    $plotPath = "data/plots/bankroll_curves/bankroll_sim_${baseName}.png"

    Write-Host "`n💰 Simulating bankroll for $file.Name"
    .venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
        --input_glob "$inputPath" `
        --output_csv "$outputCsv" `
        --plot --plot_path "$plotPath" `
        --stake_strategy kelly `
        --min_ev 0.05 `
        --max_odds 10 `
        --max_stake_frac 0.02
}
