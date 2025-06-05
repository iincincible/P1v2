import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, accuracy_score
from scripts.utils.betting_math import compute_ev, compute_kelly_stake
from tqdm import tqdm
import os

# --- Parse CLI arguments ---
parser = argparse.ArgumentParser()
parser.add_argument("--train_csvs", nargs="+", required=True)
parser.add_argument("--test_features", required=True)
parser.add_argument("--test_predictions", required=True)
parser.add_argument("--value_bets_csv", required=True)
parser.add_argument("--bankroll_csv", required=True)
parser.add_argument("--ev_threshold", type=float, default=0.0)
parser.add_argument("--max_odds", type=float, default=1000.0)
parser.add_argument("--max_margin", type=float, default=1.0)
parser.add_argument("--fixed_stake", type=float, default=10.0)
parser.add_argument("--strategy", choices=["flat", "kelly"], default="kelly")
args = parser.parse_args()

# --- Load and concatenate training data ---
train_dfs = []
for path in args.train_csvs:
    df = pd.read_csv(path)
    initial = len(df)
    df = df.dropna(subset=["odds_player_1", "odds_player_2"])
    print(f"📂 {path.split('/')[-1].replace('_features.csv','')}: {initial} → {len(df)} rows after dropna on odds")
    train_dfs.append(df)

df_train = pd.concat(train_dfs, ignore_index=True)
if df_train.empty:
    raise ValueError("❌ No training data found. All input files are empty or filtered out.")

# --- Load test data ---
df_test = pd.read_csv(args.test_features)
df_test = df_test.dropna(subset=["odds_player_1", "odds_player_2"])

# --- Train model ---
X_train = df_train[["implied_prob_1", "implied_prob_2"]]
y_train = (df_train["actual_winner"] == df_train["player_1"]).astype(int)

model = LogisticRegression()
model.fit(X_train, y_train)

# --- Predict ---
X_test = df_test[["implied_prob_1", "implied_prob_2"]]
df_test["pred_prob_player_1"] = model.predict_proba(X_test)[:, 1]

# --- Evaluate and save predictions ---
if "actual_winner" in df_test.columns:
    y_test = (df_test["actual_winner"] == df_test["player_1"]).astype(int)
    print(f"✅ Accuracy: {accuracy_score(y_test, df_test['pred_prob_player_1'] > 0.5):.4f}")
    print(f"✅ Log loss: {log_loss(y_test, df_test['pred_prob_player_1']):.5f}")

df_test.to_csv(args.test_predictions, index=False)
print(f"📁 Saved predictions to {args.test_predictions}")

# --- Compute expected value and filter bets ---
df_test["expected_value"] = df_test.apply(
    lambda row: compute_ev(row["pred_prob_player_1"], row["odds_player_1"]), axis=1
)

df_bets = df_test[
    (df_test["expected_value"] > args.ev_threshold) &
    (df_test["odds_margin"] < args.max_margin) &
    (df_test["odds_player_1"] <= args.max_odds)
].copy()

# --- Auto-switch to flat if too few bets ---
strategy_used = args.strategy
if args.strategy == "kelly" and len(df_bets) < 10:
    print(f"⚠️ Only {len(df_bets)} value bets — switching to flat staking for safety.")
    strategy_used = "flat"

df_bets["stake"] = args.fixed_stake if strategy_used == "flat" else df_bets.apply(
    lambda row: compute_kelly_stake(row["pred_prob_player_1"], row["odds_player_1"]),
    axis=1
)
df_bets["kelly_stake"] = df_bets.apply(
    lambda row: compute_kelly_stake(row["pred_prob_player_1"], row["odds_player_1"]),
    axis=1
)

df_bets.to_csv(args.value_bets_csv, index=False)
print(f"✅ Saved {len(df_bets)} value bets to {args.value_bets_csv}")

# --- Simulate bankroll ---
bankroll = 1000.0
peak = bankroll
drawdown = 0.0
bankroll_history = []

for _, row in tqdm(df_bets.iterrows(), total=len(df_bets), desc="Simulating bankroll"):
    stake = args.fixed_stake if strategy_used == "flat" else row["kelly_stake"]
    won = row["actual_winner"] == row["player_1"]
    payout = stake * (row["odds_player_1"] - 1) if won else -stake
    bankroll += payout
    peak = max(peak, bankroll)
    drawdown = max(drawdown, peak - bankroll)
    bankroll_history.append(bankroll)

pd.DataFrame({"bankroll": bankroll_history}).to_csv(args.bankroll_csv, index=False)
print(f"\n📈 Simulated {len(df_bets)} bets")
print(f"💰 Final bankroll: {bankroll:.2f}")
print(f"📉 Max drawdown: {drawdown:.2f}")
