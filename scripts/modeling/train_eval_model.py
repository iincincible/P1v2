import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from pathlib import Path
from tqdm import tqdm

from scripts.utils.betting_math import compute_kelly_stake, add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.cli_utils import should_run, assert_file_exists
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
    DEFAULT_STRATEGY,
    DEFAULT_FIXED_STAKE
)
from scripts.utils.filters import filter_value_bets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csvs", nargs="+", required=True, help="Training feature files")
    parser.add_argument("--test_csv", required=True, help="Testing feature file")
    parser.add_argument("--value_bets_csv", required=True)
    parser.add_argument("--bankroll_csv", required=True)
    parser.add_argument("--features", nargs="+", default=[
        "implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"
    ])
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN)
    parser.add_argument("--strategy", choices=["kelly", "flat"], default=DEFAULT_STRATEGY)
    parser.add_argument("--fixed_stake", type=float, default=DEFAULT_FIXED_STAKE)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.value_bets_csv, args.overwrite, args.dry_run):
        return
    if not should_run(args.bankroll_csv, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.test_csv, "test_csv")
    for path in args.train_csvs:
        assert_file_exists(path, "train_csv")

    # === Load training data ===
    train_dfs = []
    for path in args.train_csvs:
        try:
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = df.dropna(subset=args.features + ["actual_winner", "player_1"])
            df["label"] = (df["actual_winner"] == df["player_1"]).astype(int)
            train_dfs.append(df)
        except Exception as e:
            log_warning(f"Skipping {path} — {e}")

    if not train_dfs:
        raise ValueError("❌ No valid training files.")

    df_train = pd.concat(train_dfs, ignore_index=True)
    log_info(f"Loaded {len(df_train)} training rows")

    # === Load test data ===
    df_test = pd.read_csv(args.test_csv)
    df_test = normalize_columns(df_test)
    df_test = df_test.dropna(subset=args.features + ["odds", "player_1"])
    df_test = add_ev_and_kelly(df_test)

    # === Patch winner ===
    if "winner" not in df_test.columns:
        if "actual_winner" in df_test.columns and "player_1" in df_test.columns:
            df_test["winner"] = (
                df_test["actual_winner"].str.strip().str.lower() ==
                df_test["player_1"].str.strip().str.lower()
            ).astype(int)
            log_info("🩹 Patched 'winner' column from actual_winner")
        else:
            log_warning("⚠️ 'winner' column missing and could not be derived")

    # === Train model ===
    model = LogisticRegression()
    X_train = df_train[args.features]
    y_train = df_train["label"]
    model.fit(X_train, y_train)

    # === Predict ===
    X_test = df_test[args.features]
    df_test["predicted_prob"] = model.predict_proba(X_test)[:, 1]

    if "actual_winner" in df_test.columns:
        y_true = (df_test["actual_winner"] == df_test["player_1"]).astype(int)
        log_success(f"Accuracy: {accuracy_score(y_true, df_test['predicted_prob'] > 0.5):.4f}")
        log_success(f"Log Loss: {log_loss(y_true, df_test['predicted_prob']):.5f}")

    # === EV Filtering ===
    df_filtered = filter_value_bets(df_test, args.ev_threshold, args.max_odds, args.max_margin)

    strategy_used = args.strategy
    if args.strategy == "kelly" and len(df_filtered) < 10:
        log_warning(f"⚠️ Only {len(df_filtered)} bets — switching to flat staking")
        strategy_used = "flat"

    df_filtered["stake"] = (
        args.fixed_stake if strategy_used == "flat"
        else df_filtered["kelly_stake"]
    )

    df_filtered["kelly_stake"] = compute_kelly_stake(df_filtered["predicted_prob"], df_filtered["odds"])

    df_filtered.to_csv(args.value_bets_csv, index=False)
    log_success(f"✅ Saved {len(df_filtered)} value bets to {args.value_bets_csv}")

    # === Simulate bankroll ===
    bankroll = 1000.0
    peak = bankroll
    drawdown = 0.0
    trajectory = []

    for _, row in tqdm(df_filtered.iterrows(), total=len(df_filtered), desc="Simulating bankroll"):
        stake = args.fixed_stake if strategy_used == "flat" else row["kelly_stake"]
        won = row.get("actual_winner", "").strip().lower() == row.get("player_1", "").strip().lower()
        payout = stake * (row["odds"] - 1) if won else -stake
        bankroll += payout
        peak = max(peak, bankroll)
        drawdown = max(drawdown, peak - bankroll)
        trajectory.append(bankroll)

    pd.DataFrame({"bankroll": trajectory}).to_csv(args.bankroll_csv, index=False)
    log_success(f"💰 Final bankroll: {bankroll:.2f}")
    log_success(f"📉 Max drawdown: {drawdown:.2f}")

if __name__ == "__main__":
    main()
