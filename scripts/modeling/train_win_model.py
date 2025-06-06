import argparse
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", default="data/processed/*_features.csv")
    parser.add_argument("--output_model", default="modeling/win_model.pkl")
    parser.add_argument("--min_rows", type=int, default=30)
    args = parser.parse_args()

    import glob
    files = glob.glob(args.input_glob)
    dfs = []

    for f in files:
        df = pd.read_csv(f)
        if "actual_winner" in df.columns and "player_1" in df.columns:
            df["label"] = (df["actual_winner"] == df["player_1"]).astype(int)
            dfs.append(df)

    full = pd.concat(dfs, ignore_index=True)
    full = full.dropna(subset=[
        "odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff", "label"
    ])
    print(f"✅ Loaded {len(full)} rows across {len(files)} files")

    X = full[["odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff"]]
    y = full["label"]

    model = LogisticRegression(solver="liblinear")
    acc = cross_val_score(model, X, y, cv=5, scoring="accuracy").mean()
    ll = -cross_val_score(model, X, y, cv=5, scoring="neg_log_loss").mean()

    print(f"📊 CV Accuracy: {acc:.4f}")
    print(f"📉 CV Log Loss: {ll:.4f}")

    model.fit(X, y)
    Path(args.output_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output_model)
    print(f"💾 Saved model to {args.output_model}")

if __name__ == "__main__":
    main()
