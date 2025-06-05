import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.input_csv)
    if "actual_winner" not in df.columns or "player_1" not in df.columns:
        raise ValueError("Input must contain 'actual_winner' and 'player_1' columns")

    # Label: 1 if player_1 won
    df["player_1_won"] = (df["actual_winner"] == df["player_1"]).astype(int)

    # Features
    X = df[["odds_player_1", "odds_player_2", "implied_prob_1", "implied_prob_2", "odds_margin", "implied_diff"]]
    y = df["player_1_won"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # Train logistic regression
    model = LogisticRegression(solver="liblinear")
    model.fit(X_train, y_train)

    # Predict win probabilities
    df["pred_prob_player_1"] = model.predict_proba(X)[:, 1]

    # 🔒 Clip extreme predictions to prevent simulation distortion
    df["pred_prob_player_1"] = df["pred_prob_player_1"].clip(0.05, 0.95)

    # Save predictions
    df.to_csv(args.output_csv, index=False)

    # Report metrics
    acc = accuracy_score(y, model.predict(X))
    logloss = log_loss(y, model.predict_proba(X)[:, 1])
    print(f"✅ Saved predictions to {args.output_csv}")
    print(f"📊 Accuracy: {acc:.4f}, Log Loss: {logloss:.4f}")

if __name__ == "__main__":
    main()
