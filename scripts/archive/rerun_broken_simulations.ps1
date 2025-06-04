# scripts/rerun_broken_simulations.ps1
.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_atp_aus_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_atp_aus_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_atp_aus_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02

.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_atp_french_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_atp_french_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_atp_french_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02

.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_atp_us_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_atp_us_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_atp_us_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02

.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_wta_aus_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_wta_aus_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_wta_aus_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02

.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_wta_french_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_wta_french_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_wta_french_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02

.venv\Scripts\python.exe scripts/simulate_bankroll_growth.py `
  --input_glob "data/processed/value_bets_wta_us_open_2023_deduped.csv" `
  --output_csv "data/processed/bankroll_sim_wta_us_open_2023_deduped.csv" `
  --plot --plot_path "data/plots/bankroll_curves/bankroll_sim_wta_us_open_2023.png" `
  --stake_strategy kelly `
  --min_ev 0.05 `
  --max_odds 10 `
  --max_stake_frac 0.02
