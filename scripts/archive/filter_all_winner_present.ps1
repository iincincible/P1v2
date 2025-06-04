$files = @(
    "merged_atp_aus_open_2023_deduped.csv",
    "merged_atp_french_open_2023_deduped.csv",
    "merged_atp_us_open_2023_deduped.csv",
    "merged_atp_wimbledon_2023_deduped.csv",
    "merged_wta_aus_open_2023_deduped.csv",
    "merged_wta_french_open_2023_deduped.csv",
    "merged_wta_us_open_2023_deduped.csv",
    "merged_wta_wimbledon_2023_deduped.csv"
)

foreach ($file in $files) {
    $input = "data/processed/$file"
    $output = $input -replace '\.csv$', '_filtered.csv'
    Write-Host "📂 Creating 'winner_name' and filtering → $(Split-Path $output -Leaf)"

    .venv\Scripts\python.exe -c "
import pandas as pd
df = pd.read_csv('$input')
df['winner_name'] = df.apply(lambda row: row['player_1'] if row.get('p1_is_winner') else (row['player_2'] if row.get('p2_is_winner') else None), axis=1)
df = df[df['winner_name'].notna() & (df['winner_name'] != '')]
df.to_csv('$output', index=False)
"
}
