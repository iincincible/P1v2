import argparse
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csvs", nargs="+", required=True)
    parser.add_argument("--model_output", required=True)
    args = parser.parse_args()

    dfs = [pd.read_csv(path) for path in args.train_csvs]
    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(subset=["implied_prob_1", "implied_prob_2", "actual_winner", "player_1"])

    X = df[["implied_prob_1", "implied_prob_2"]]
    y = (df["actual_winner"] == df["player_1"]).astype(int)

    model = LogisticRegression(solver="liblinear")
    model.fit(X, y)

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    print(f"✅ Accuracy: {accuracy_score(y, y_pred):.4f}")
    print(f"✅ Log Loss: {log_loss(y, y_prob):.5f}")

    joblib.dump(model, args.model_output)
    print(f"✅ Saved model to {args.model_output}")

if __name__ == "__main__":
    main()
