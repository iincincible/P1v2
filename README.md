# P1v2 — Tennis Grand Slam Value Betting Model (ATP)

This repository contains a full pipeline to detect and simulate value bets across ATP Grand Slam tournaments using Betfair Exchange data and Jeff Sackmann’s tennis match results.

## ✅ Completed Pipeline

The following ATP 2023 Grand Slam tournaments are fully processed:

| Tournament         | Data Parsed | Modeling Complete | Value Bets | Bankroll Simulated |
|-------------------|-------------|-------------------|------------|---------------------|
| Australian Open   | ✅           | ✅                 | ✅          | ✅                  |
| French Open       | ✅           | ✅                 | ✅          | ✅                  |
| Wimbledon         | ✅           | ✅                 | ✅          | ✅                  |
| US Open           | ✅           | ✅                 | ✅          | ✅                  |

## 🧠 Model Strategy

- Logistic regression trained on odds from prior Slams
- LTPs used to calculate implied probabilities
- Value bets filtered by:
  - Expected value threshold
  - Max odds
  - Max market overround

## 🧪 Evaluation

Final bankroll result on US Open (cross-slam evaluation):
- 📉 **ROI: -54.2%** (Final bankroll: $-5420.00 on 642 bets)

## 📂 Project Structure

```
P1v2/
├── data/
│   └── processed/                 # Merged, enriched, and feature CSVs
├── parsed/                        # Parsed Betfair snapshots
├── modeling/                      # Output of bankroll simulations
├── scripts/                       # All modular pipeline scripts
└── README.md                      # This file
```

## 🔁 One-Command Pipeline

The full pipeline for a tournament includes:

```bash
# Example: US Open
python scripts/parse_betfair_snapshots.py ...
python scripts/merge_sackmann_with_snapshots.py ...
python scripts/match_selection_ids.py ...
python scripts/merge_ltps_by_ids.py ...
python scripts/build_clean_matches_usopen_2023_atp.py
python scripts/build_odds_features.py ...
python scripts/train_eval_model_cross_slam.py ...
```

## 🛠️ Dependencies

- Python 3.10+
- pandas, scikit-learn, numpy, tqdm, thefuzz

Install with:

```bash
pip install -r requirements.txt
```
