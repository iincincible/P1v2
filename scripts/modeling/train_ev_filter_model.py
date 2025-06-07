import argparse
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.filters import filter_value_bets
from scripts.utils.logger import log_info, log_success, log_warning, log_error

parser = argparse.ArgumentParser()
parser.add_argument("--input_files", nargs='+', required=True)
parser.add_argument("--output_model", required=True)
parser.add_argument("--min_ev", type=float, default=0.2)
args = parser.parse_args()

rows = []
for file in args.input_files:
    try:
        df = pd.read_csv(file)
        df = normalize_columns(df)
        df = add_ev_and_kelly(df)
        df = df[df["expected_value"] >= args.min_ev]

        if "winner" not in df.columns:
            log_warning(f"No 'winner' column in {file}, using synthetic EV label.")
            df["winner"] = (df["expected_value"] > 0).astype(int)

        rows.append(df)
        log_info(f"Loaded {len(df)} rows from {file}")
    except Exception as e:
        log_error(f"Failed to load {file}: {e}")

if not rows:
    raise ValueError("❌ All input files failed to load or were empty.")

df = pd.concat(rows, ignore_index=True)
log_success(f"Training on {len(df)} rows (EV ≥ {args.min_ev})")

features = ["predicted_prob", "odds", "expected_value"]
X = df[features]
y = df["winner"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.25, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

log_info("📊 Classification report on holdout set:")
print(classification_report(y_test, model.predict(X_test)))

Path(args.output_model).parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, args.output_model)
log_success(f"Saved EV filter model to {args.output_model}")
