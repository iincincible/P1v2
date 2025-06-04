# scripts/rerun_model_and_value_bets.ps1

# 🧠 ATP Australian Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_atp_aus_open_2023_deduped.csv `
  --output_csv data/processed/predictions_atp_aus_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_atp_aus_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_atp_aus_open_2023_deduped.csv

# 🎾 ATP French Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_atp_french_open_2023_deduped.csv `
  --output_csv data/processed/predictions_atp_french_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_atp_french_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_atp_french_open_2023_deduped.csv

# 🇺🇸 ATP US Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_atp_us_open_2023_deduped.csv `
  --output_csv data/processed/predictions_atp_us_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_atp_us_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_atp_us_open_2023_deduped.csv

# 🧠 WTA Australian Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_wta_aus_open_2023_deduped.csv `
  --output_csv data/processed/predictions_wta_aus_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_wta_aus_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_wta_aus_open_2023_deduped.csv

# 🎾 WTA French Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_wta_french_open_2023_deduped.csv `
  --output_csv data/processed/predictions_wta_french_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_wta_french_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_wta_french_open_2023_deduped.csv

# 🇺🇸 WTA US Open
.venv\Scripts\python.exe scripts/train_win_model_from_odds.py `
  --input_csv data/processed/merged_wta_us_open_2023_deduped.csv `
  --output_csv data/processed/predictions_wta_us_open_2023_deduped.csv `
  --preserve_winner_name

.venv\Scripts\python.exe scripts/detect_value_bets.py `
  --input_csv data/processed/predictions_wta_us_open_2023_deduped.csv `
  --output_csv data/processed/value_bets_wta_us_open_2023_deduped.csv
