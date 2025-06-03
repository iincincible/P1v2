P1v2 — Tennis Predictive Betting Model
Overview
P1v2 is a data pipeline and predictive model for tennis betting, focused initially on the 2023 Australian Open. The project processes Betfair snapshot data and player match metadata to build odds-based features and train a logistic regression model that predicts match winners.

Current Status
Full data parsing pipeline for Betfair tennis snapshots and match metadata

Robust matching and enrichment of player IDs and selection IDs

Odds feature engineering with support for multiple column suffixes (_x, _y)

Balanced dataset creation with player order normalization and binary win labels

Logistic regression model trained on balanced dataset with baseline accuracy (~50%)

Next planned phases: value bet detection, expected value calculation, and bankroll simulation

Installation
Create a Python virtual environment and install dependencies:

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

Usage
Running the pipeline
Build clean snapshot matches:

python scripts/build_clean_matches_from_snapshots.py

Build odds features:

python scripts/build_odds_features.py --input_csv data/processed/ausopen_2023_clean_snapshot_matches.csv --output_csv data/processed/ausopen_2023_features.csv --cap 10.0

Expand and balance dataset:

python scripts/expand_and_balance_dataset.py

Train the logistic regression win model:

python scripts/train_win_model_from_odds.py --input_csv data/processed/ausopen_2023_features_expanded.csv --output_csv data/processed/ausopen_2023_model_preds.csv

Data
Raw data (e.g., .bz2 snapshot archives) and large files are excluded via .gitignore

Processed datasets and outputs are stored under data/processed/

Contributing
Feel free to open issues or pull requests for improvements.

License
MIT License

Contact
GitHub: puntingpro