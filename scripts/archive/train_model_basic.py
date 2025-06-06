import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
import joblib

def load_data(csv_paths):
    dfs = []
    for path in csv_paths:
        df = pd.read_csv(path)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csvs", nargs="+", required=True, help="List of CSVs for training")
    parser.add_argument("--model_output", type=str, required=True, help="Path to save model")
    args = parser.parse_args()

    df = load_data(args.train_csvs)

    required_cols = [
        "implied_prob_1",
        "implied_prob_2",
        "implied_diff",
        "odds_player_1",
        "odds_player_2",
        "odds_margin",
        "won"
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in training data: {missing_cols}")

    X = df[["implied_prob_1", "implied_prob_2", "implied_diff", "odds_player_1", "odds_player_2", "odds_margin"]]
    y = df["won"]

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    preds = model.predict_proba(X)
    pred_labels = model.predict(X)

    acc = accuracy_score(y, pred_labels)
    ll = log_loss(y, preds)

    print(f"✅ Accuracy: {acc:.4f}")
    print(f"✅ Log Loss: {ll:.5f}")

    joblib.dump(model, args.model_output)
    print(f"✅ Saved model to {args.model_output}")

if __name__ == "__main__":
    main()
