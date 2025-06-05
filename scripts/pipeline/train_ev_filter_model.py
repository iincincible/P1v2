import argparse
import pandas as pd
import glob
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", default="data/processed/*_predictions.csv")
    parser.add_argument("--output_model", default="modeling/ev_filter_model.pkl")
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    args = parser.parse_args()

    required_cols = {
        "pred_prob_player_1", "odds_player_1", "odds_player_2",
        "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff",
        "actual_winner", "player_1"
    }

    files = glob.glob(args.input_glob)
    dfs = []
    skipped = 0

    for file in files:
        df = pd.read_csv(file, low_memory=False)
        if not required_cols.issubset(set(df.columns)):
            print(f"⚠️ Skipping {file} — missing required columns")
            skipped += 1
            continue

        df["ev"] = (df["pred_prob_player_1"] * df["odds_player_1"]) - 1
        df = df[df["ev"] > args.ev_threshold].copy()
        df["bet_success"] = (df["actual_winner"] == df["player_1"]).astype(int)
        dfs.append(df)

    if not dfs:
        raise ValueError("❌ No valid files found. All skipped or empty.")

    data = pd.concat(dfs, ignore_index=True)
    print(f"✅ Loaded {len(data)} EV bet rows from {len(files) - skipped} valid files")

    features = [
        "pred_prob_player_1", "odds_player_1", "odds_player_2",
        "implied_prob_1", "implied_prob_2", "odds_margin",
        "implied_diff", "ev"
    ]

    X = data[features]
    y = data["bet_success"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    acc = cross_val_score(model, X, y, cv=5, scoring="accuracy").mean()
    ll = -cross_val_score(model, X, y, cv=5, scoring="neg_log_loss").mean()
    print(f"📊 CV Accuracy: {acc:.4f}")
    print(f"📉 CV Log Loss: {ll:.4f}")

    model.fit(X, y)
    Path(args.output_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output_model)
    print(f"💾 Saved EV filter model to {args.output_model}")

if __name__ == "__main__":
    main()
