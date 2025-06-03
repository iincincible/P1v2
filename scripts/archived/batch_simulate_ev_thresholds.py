import subprocess
from pathlib import Path

# Settings
input_csv = "data/processed/value_bets_frenchopen_2023.csv"
output_dir = Path("data/plots/bankroll_curves/batch_ev_thresholds")
output_dir.mkdir(parents=True, exist_ok=True)

ev_thresholds = [0.05, 0.01, 0.005, 0.001]
odds_caps = [10, 20, 1000]

for ev in ev_thresholds:
    for cap in odds_caps:
        output_csv = output_dir / f"bankroll_ev{ev}_cap{cap}.csv"
        plot_path = output_dir / f"bankroll_ev{ev}_cap{cap}.png"
        print(f"▶️ Simulating EV ≥ {ev}, Odds Cap = {cap}")
        subprocess.run([
            "python", "scripts/simulate_bankroll_growth.py",
            "--input_csvs", input_csv,
            "--output_csv", str(output_csv),
            "--plot",
            "--plot_path", str(plot_path),
            "--ev_threshold", str(ev),
            "--odds_cap", str(cap)
        ])