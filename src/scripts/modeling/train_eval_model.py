import argparse
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import (
    add_common_flags,
    should_run,
    assert_file_exists,
    assert_columns_exist,
)
from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.filters import filter_value_bets
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN,
    DEFAULT_FIXED_STAKE,
    DEFAULT_STRATEGY,
)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Train and evaluate win probability model, then simulate bankroll."
    )
    parser.add_argument(
        "--train_csvs", nargs="+", required=True, help="List of CSVs for training"
    )
    parser.add_argument("--test_csv", required=True, help="CSV for model testing")
    parser.add_argument(
        "--value_bets_csv", required=True, help="Path to save filtered value bets"
    )
    parser.add_argument(
        "--bankroll_csv", required=True, help="Path to save bankroll simulation CSV"
    )
    parser.add_argument(
        "--features",
        nargs="+",
        default=[
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ],
        help="Feature columns for model",
    )
    parser.add_argument(
        "--output_model",
        default="modeling/win_model.pkl",
        help="Where to save the trained win probability model"
    )
    parser.add_argument(
        "--ev_threshold",
        type=float,
        default=DEFAULT_EV_THRESHOLD,
        help="EV threshold for filtering bets",
    )
    parser.add_argument(
        "--max_odds",
        type=float,
        default=DEFAULT_MAX_ODDS,
        help="Maximum odds to include",
    )
    parser.add_argument(
        "--max_margin",
        type=float,
        default=DEFAULT_MAX_MARGIN,
        help="Maximum odds margin for bets",
    )
    parser.add_argument(
        "--strategy",
        choices=["flat", "kelly"],
        default=DEFAULT_STRATEGY,
        help="Staking strategy for simulation",
    )
    parser.add_argument(
        "--fixed_stake",
        type=float,
        default=DEFAULT_FIXED_STAKE,
        help="Fixed stake amount if using flat strategy",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    # Dry-run
    if _args.dry_run:
        log_dryrun(
            f"Would train on {len(_args.train_csvs)} CSV(s), evaluate on {_args.test_csv}, "
            f"filter EV ≥ {_args.ev_threshold}, odds ≤ {_args.max_odds}, margin ≤ {_args.max_margin}, "
            f"then simulate with {_args.strategy} staking → "
            f"{_args.value_bets_csv}, { _args.bankroll_csv }"
        )
        return

    # Check outputs
    vb_path = Path(_args.value_bets_csv)
    br_path = Path(_args.bankroll_csv)
    if not should_run(vb_path, _args.overwrite, _args.dry_run):
        return
    if not should_run(br_path, _args.overwrite, _args.dry_run):
        return

    # Load & prepare training data
    train_frames = []
    for path in _args.train_csvs:
        try:
            assert_file_exists(path, "train_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = patch_winner_column(df)
            df = df.dropna(subset=_args.features + ["winner"])
            df["label"] = (df["winner"] == 1).astype(int)
            assert_columns_exist(df, _args.features + ["label"], context=path)
            train_frames.append(df)
            log_info(f"✅ Loaded {len(df)} rows from {path}")
        except Exception as e:
            log_warning(f"⚠️ Skipping training file {path}: {e}")

    if not train_frames:
        log_error("❌ No valid training data found.")
        return

    df_train = pd.concat(train_frames, ignore_index=True)
    log_success(f"📊 Training on {len(df_train)} rows")

    # Load & prepare test data
    try:
        assert_file_exists(_args.test_csv, "test_csv")
        df_test = pd.read_csv(_args.test_csv)
        df_test = normalize_columns(df_test)
        df_test = patch_winner_column(df_test)
        df_test = df_test.dropna(subset=_args.features + ["odds"])
        assert_columns_exist(
            df_test,
            _args.features + ["odds"],
            context="test set",
        )
        log_info(f"📥 Loaded {len(df_test)} test rows from {_args.test_csv}")
    except Exception as e:
        log_error(f"❌ Failed to prepare test data: {e}")
        return

    # Train & predict
    try:
        model = LogisticRegression(max_iter=1000)
        model.fit(df_train[_args.features], df_train["label"])
        df_test["predicted_prob"] = model.predict_proba(df_test[_args.features])[:, 1]
        log_success("✅ Model trained and predictions made")
        # Save the trained model
        joblib.dump(model, _args.output_model)
        log_success(f"💾 Trained model saved to {_args.output_model}")
        # Optional metrics
        if "winner" in df_test.columns:
            y_true = (df_test["winner"] == 1).astype(int)
            acc = accuracy_score(y_true, df_test["predicted_prob"] > 0.5)
            loss = log_loss(y_true, df_test["predicted_prob"])
            log_info(f"🎯 Accuracy: {acc:.4f}, LogLoss: {loss:.5f}")
    except Exception as e:
        log_error(f"❌ Training/prediction failed: {e}")
        return

    # Add EV and Kelly columns (if not present)
    try:
        from scripts.utils.betting_math import add_ev_and_kelly
        df_test = add_ev_and_kelly(df_test, prob_col="predicted_prob", odds_col="odds")
    except Exception as e:
        log_error(f"❌ Could not add expected_value/Kelly: {e}")
        return

    # Filter value bets
    try:
        df_filtered = filter_value_bets(
            df_test, _args.ev_threshold, _args.max_odds, _args.max_margin
        )
        log_success(f"✅ Filtered {len(df_filtered)} value bets")
    except Exception as e:
        log_error(f"❌ Value bet filtering failed: {e}")
        return

    # Write value bets CSV
    try:
        vb_path.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(vb_path, index=False)
        log_success(f"📝 Saved value bets to {vb_path}")
    except Exception as e:
        log_error(f"❌ Failed to save value bets: {e}")
        return

    # Simulate bankroll
    try:
        sim_df, final_bankroll, max_drawdown = simulate_bankroll(
            df_filtered,
            strategy=_args.strategy,
            initial_bankroll=1000.0,
            ev_threshold=0.0,
            odds_cap=100.0,
            cap_fraction=0.05,
        )
        log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
        log_info(f"📉 Max drawdown: {max_drawdown:.2f}")
        # Save bankroll CSV
        br_path.parent.mkdir(parents=True, exist_ok=True)
        sim_df.to_csv(br_path, index=False)
        log_success(f"✅ Saved bankroll simulation to {br_path}")
        # Plot
        plot_path = br_path.with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=plot_path)
        log_success(f"🖼️ Saved bankroll plot to {plot_path}")
    except Exception as e:
        log_error(f"❌ Simulation or saving failed: {e}")


if __name__ == "__main__":
    main()
