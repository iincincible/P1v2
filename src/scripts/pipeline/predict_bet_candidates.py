import pandas as pd
import joblib

# Load candidates
df = pd.read_csv("data/processed/ausopen_2023_atp_bet_candidates.csv")

# Load your trained model
model = joblib.load(r"C:\Users\lucap\Projects\P1v2\modeling\win_model.pkl")

# Use the features your model expects
features = ["implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"]
X = df[features]

# Get predicted probabilities (for "player_1" win)
if hasattr(model, "predict_proba"):
    df["predicted_prob"] = model.predict_proba(X)[:, 1]
else:
    df["predicted_prob"] = model.predict(X)

# Save the enriched file
df.to_csv("data/processed/ausopen_2023_atp_bet_candidates_with_preds.csv", index=False)
print(
    "Saved predictions to data/processed/ausopen_2023_atp_bet_candidates_with_preds.csv"
)
