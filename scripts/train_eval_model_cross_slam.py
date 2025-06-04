import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
import numpy as np
import argparse
import os
from tqdm import tqdm

# === CLI Args ===
parser = argparse.ArgumentParser()
parser.add_argument("--ausopen_csv", default="data/processed/ausopen_2023_atp_predictions.csv")
parser.add_argument("--frenchopen_csv", default="data/processed/frenchopen_2023_atp_predictions.csv")
parser.add_argument("--wimbledon_csv", default="data/processed/wimbledon_2023_atp_predictions.csv")
parser.add_argument("--test_features", default="data/processed/usopen_2023_atp_features.csv")
parser.add_argument("--test_predictions", default="data/processed/usopen_2023_atp_predictions.csv")
parser.add_argument("--value_bets_csv", default="data/processed/value_bets_usopen_2023_atp.csv")
parser.add_argument("--bankroll_csv", default="modeling/usopen_2023_atp_bankroll.csv")
parser.add_argument("--ev_threshold", type=float, default=0.0)
parser.add_argument("--max_odds", type=float, default=10.0)
parser.add_argument("--max_margin", type=float, default=0.10)
parser.add_argument("--fixed_stake", type=float, default=10.0)
args = parser.parse_args()

# === Load and merge training data ===
df_ao = pd.read_csv(args.ausopen_csv)
df_fo = pd.read_csv(args.frenchopen_csv)
df_wb = pd.read_csv(args.wimbledon_csv)
df_train = pd.concat([df_ao, df_fo, df_wb], ignore_index=True)

df_train["label"] = (df_train["actual_winner"] == df_train["player_1"]).astype(int)
df_train = df_train.dropna(subset=["odds_player_1", "odds_player_2"])

X_train = df_train[["odds_player_1", "odds_player_2"]]
y_train = df_train["label"]

# === Train model ===
model = LogisticRegression()
model.fit(X_train, y_train)
print("✅ Trained on", len(df_train), "matches")

# === Load test features ===
df_test = pd.read_csv(args.test_features)
df_test["odds_player_1"] = pd.to_numeric(df_test["odds_player_1"], errors="coerce")
df_test["odds_player_2"] = pd.to_numeric(df_test["odds_player_2"], errors="coerce")
df_test = df_test.dropna(subset=["odds_player_1", "odds_player_2"])

X_test = df_test[["odds_player_1", "odds_player_2"]]
df_test["pred_prob_player_1"] = model.predict_proba(X_test)[:, 1]
df_test.to_csv(args.test_predictions, index=False)
print("📁 Saved predictions to", args.test_predictions)

# === Compute expected value ===
for i in [1, 2]:
    prob_col = df_test["pred_prob_player_1"] if i == 1 else (1 - df_test["pred_prob_player_1"])
    odds_col = f"odds_player_{i}"
    df_test[f"ev_player_{i}"] = prob_col * (df_test[odds_col] - 1) - (1 - prob_col)

# === Detect value bets ===
bets = []
for _, row in df_test.iterrows():
    for i in [1, 2]:
        prob = row["pred_prob_player_1"] if i == 1 else 1 - row["pred_prob_player_1"]
        odds = row[f"odds_player_{i}"]
        margin = abs((1 / row["odds_player_1"]) + (1 / row["odds_player_2"]) - 1)
        ev = row[f"ev_player_{i}"]
        if ev > args.ev_threshold and odds <= args.max_odds and margin <= args.max_margin:
            bets.append({
                "match_id": row.get("match_id", None),
                "player": row[f"player_{i}"],
                "odds": odds,
                "pred_prob": prob,
                "ev": ev,
                "actual_winner": row.get("actual_winner", None),
                "won": row.get(f"player_{i}") == row.get("actual_winner") if "actual_winner" in row else None
            })

bets_df = pd.DataFrame(bets)
bets_df.to_csv(args.value_bets_csv, index=False)
print(f"✅ Saved {len(bets_df)} value bets to {args.value_bets_csv}")

# === Simulate bankroll growth ===
bankroll = 1000.0
peak = 1000.0
history = []

for _, row in tqdm(bets_df.iterrows(), total=len(bets_df), desc="Simulating bankroll"):
    stake = args.fixed_stake
    win = row["won"]
    payout = stake * row["odds"] if win else 0
    bankroll += payout - stake
    peak = max(peak, bankroll)
    drawdown = peak - bankroll
    history.append({"bankroll": bankroll, "drawdown": drawdown})

bankroll_df = pd.DataFrame(history)
bankroll_df.to_csv(args.bankroll_csv, index=False)

print(f"\n📈 Simulated {len(bets_df)} bets")
print(f"💰 Final bankroll: {bankroll:.2f}")
print(f"📉 Max drawdown: {bankroll_df['drawdown'].max():.2f}")
