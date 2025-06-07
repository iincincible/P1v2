import argparse
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from tqdm import tqdm

from scripts.utils.betting_math import compute_kelly_stake, add_ev_and_kelly
from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags, assert_columns_exist
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
    DEFAULT_STRATEGY,
    DEFAULT_FIXED_STAKE
)
from scripts.utils.filters import filter_value_bets
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate win prob model. Simulate bankroll as well.")
    parser.add_argument("--train_csvs", nargs="+", required=True, help="Training feature files")
    parser.add_argument("--test_csv", required=True, help="Testing feature file")
    parser.add_argument("--value_bets_csv", required=True, help="Output filtered bets CSV")
    parser.add_argument("--bankroll_csv", required=True, help="Output bankroll trajectory CSV")
    parser.add_argument("--features", nargs="+", default=[
        "implied_prob_1", "implied_prob_2", "implied_prob_diff", "odds_margin"
    ])
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN)
    parser.add_argument("--strategy", choices=["kelly", "flat"], default=DEFAULT_STRATEGY)
    parser.add_argument("--fixed_stake", type=float, default=DEFAULT_FIXED_STAKE)
    add_common_flags(parser)
    args = parser.parse_args()

    value_bets_path = Path(args.value_bets_csv)
    bankroll_path = Path(args.bankroll_csv)

    if not should_run(value_bets_path, args.overwrite, args.dry_run):
        return
    if not should_run(bankroll_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.test_csv, "test_csv")
    for path in args.train_csvs:
        assert_file_exists(path, "train_csv")

    train_dfs = []
    for path in args.train_csvs:
        try:
            df = pd.read_csv(path)
            df = normalize_columns(df)
            before = len(df)
            df = df.dropna(subset=args.features + ["actual_winner", "player_1"])
            dropped = before - len(df)
            if dropped > 0:
                log_warning(f"⚠️ Dropped {dropped} rows with missing training data from {path}")
            df["label"] = (df["actual_winner"] == df["player_1"]).astype(int)
            assert_columns_exist(df, args.features + ["label"], context="training")
            train_dfs.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {path} — {e}")

    if not train_dfs:
        raise ValueError("❌ No valid training files.")

    df_train = pd.concat(train_dfs, ignore_index=True)
    log_info(f"✅ Loaded {len(df_train)} training rows")

    df_test = pd.read_csv(args.test_csv)
    df_test = normalize_columns(df_test)
    before_test = len(df_test)
    df_test = df_test.dropna(subset=args.features)
    dropped_test = before_test - len(df_test)
    if dropped_test > 0:
        log_warning(f"⚠️ Dropped {dropped_test} test rows due to missing features")

    df_test = add_ev_and_kelly(df_test)
    df_test = patch_winner_column(df_test)

    assert_columns_exist(df_test, args.features + ["predicted_prob", "odds", "expected_value"], context="test set")

    model = LogisticRegression()
    X_train = df_train[args.features]
    y_train = df_train["label"]
    model.fit(X_train, y_train)

    X_test = df_test[args.features]
    df_test["predicted_prob"] = model.predict_proba(X_test)[:, 1]

    if "actual_winner" in df_test.columns:
        y_true = (df_test["actual_winner"] == df_test["player_1"]).astype(int)
        acc = accuracy_score(y_true, df_test["predicted_prob"] > 0.5)
        loss = log_loss(y_true, df_test["predicted_prob"])
        log_success(f"🎯 Accuracy: {acc:.4f}")
        log_success(f"🧮 Log Loss: {loss:.5f}")

    df_filtered = filter_value_bets(df_test, args.ev_threshold, args.max_odds, args.max_margin)

    strategy_used = args.strategy
    if args.strategy == "kelly" and len(df_filtered) < 10:
        log_warning(f"⚠️ Only {len(df_filtered)} bets — switching to flat staking")
        strategy_used = "flat"

    df_filtered["kelly_stake"] = compute_kelly_stake(df_filtered["predicted_prob"], df_filtered["odds"])
    df_filtered["stake"] = (
        args.fixed_stake if strategy_used == "flat" else df_filtered["kelly_stake"]
    )

    value_bets_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(value_bets_path, index=False)
    log_success(f"✅ Saved {len(df_filtered)} value bets to {value_bets_path}")

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df_filtered,
        strategy=strategy_used,
        initial_bankroll=1000.0,
        ev_threshold=0.0,
        odds_cap=100.0,
        cap_fraction=0.05
    )

    bankroll_path.parent.mkdir(parents=True, exist_ok=True)
    sim_df.to_csv(bankroll_path, index=False)
    log_success(f"💰 Final bankroll: {final_bankroll:.2f}")
    log_success(f"📉 Max drawdown: {max_drawdown:.2f}")

    png_path = bankroll_path.with_suffix(".png")
    generate_bankroll_plot(sim_df["bankroll"], output_path=png_path)


if __name__ == "__main__":
    main()
