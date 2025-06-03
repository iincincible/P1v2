import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, accuracy_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv, low_memory=False)

    # Detect columns
    odds1_col = next((c for c in df.columns if c.startswith("odds_player_1")), None)
    odds2_col = next((c for c in df.columns if c.startswith("odds_player_2")), None)

    if not odds1_col or not odds2_col:
        raise ValueError("❌ Required odds columns not found.")

    df["odds_player_1"] = df[odds1_col]
    df["odds_player_2"] = df[odds2_col]

    # Swap odds if actual winner is player_2
    mask = df["actual_winner"] == df["player_2"]
    df.loc[mask, ["odds_player_1", "odds_player_2"]] = df.loc[mask, ["odds_player_2", "odds_player_1"]].values

    # Drop rows with NaNs in odds
    df = df.dropna(subset=["odds_player_1", "odds_player_2"])
    print(f"🧹 Dropped to {len(df)} rows with complete data")

    # Compute features
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
    df["implied_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    # Target: player_1 is winner (1 if yes, 0 if not)
    df["label"] = (df["actual_winner"] == df["player_1"]).astype(int)

    # Filter again after feature creation
    df = df.dropna(subset=["implied_diff", "odds_margin", "label"])
    if df["label"].nunique() < 2:
        raise ValueError("❌ Not enough class variation to train a model.")

    # Train model
    X = df[["implied_diff", "odds_margin"]]
    y = df["label"]
    model = LogisticRegression()
    model.fit(X, y)

    # Predict and save results
    df["pred_prob_player_1"] = model.predict_proba(X)[:, 1]
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

    # Report
    acc = accuracy_score(y, model.predict(X))
    loss = log_loss(y, df["pred_prob_player_1"])
    print(f"📊 Accuracy: {acc:.4f}, Log Loss: {loss:.4f}")

if __name__ == "__main__":
    main()
