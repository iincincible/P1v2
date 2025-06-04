import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv, low_memory=False)

    # Detect and load raw odds columns
    odds1_col = next((c for c in df.columns if c.startswith("odds_player_1")), None)
    odds2_col = next((c for c in df.columns if c.startswith("odds_player_2")), None)
    if not odds1_col or not odds2_col:
        raise ValueError("❌ Required odds columns not found.")

    df["odds_player_1"] = pd.to_numeric(df[odds1_col], errors="coerce")
    df["odds_player_2"] = pd.to_numeric(df[odds2_col], errors="coerce")

    # Drop rows with invalid odds
    df = df.dropna(subset=["odds_player_1", "odds_player_2"])
    print(f"🧹 Dropped to {len(df)} rows with valid odds")

    # Compute implied probabilities and features
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
    df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]
    df["log_odds_diff"] = np.log(df["odds_player_1"] / df["odds_player_2"])
    df["is_fav_player_1"] = (df["odds_player_1"] < df["odds_player_2"]).astype(int)

    # Target label
    df["label"] = (df["actual_winner"] == df["player_1"]).astype(int)
    df = df.dropna(subset=["label"])
    if df["label"].nunique() < 2:
        raise ValueError("❌ Not enough class variation to train.")

    # Final feature set
    features = [
        "implied_prob_diff",
        "odds_margin",
        "odds_player_1",
        "odds_player_2",
        "log_odds_diff",
        "is_fav_player_1"
    ]

    X = df[features]
    y = df["label"]

    # Train Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Predict win probability for player_1
    df["pred_prob_player_1"] = model.predict_proba(X)[:, 1]
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved predictions to {args.output_csv}")

    acc = accuracy_score(y, model.predict(X))
    loss = log_loss(y, df["pred_prob_player_1"])
    print(f"📊 Accuracy: {acc:.4f}, Log Loss: {loss:.4f}")

if __name__ == "__main__":
    main()
