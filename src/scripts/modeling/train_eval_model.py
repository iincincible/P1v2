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
    output_file_guard,
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

@output_file_guard(output_arg="value_bets_csv")
def train_eval_model(
    train_csvs,
    test_csv,
    value_bets_csv,
    bankroll_csv,
    features,
    output_model,
    ev_threshold=DEFAULT_EV_THRESHOLD,
    max_odds=DEFAULT_MAX_ODDS,
    max_margin=DEFAULT_MAX_MARGIN,
    strategy=DEFAULT_STRATEGY,
    fixed_stake=DEFAULT_FIXED_STAKE,
    overwrite=False,
    dry_run=False,
):
    # Load & prepare training data
    train_frames = []
    for path in train_csvs:
        try:
            assert_file_exists(path, "train_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = patch_winner_column(df)
            df = df.dropna(subset=features + ["winner"])
            df["label"] = (df["winner"] == 1).astype(int)
            assert_columns_exist(df, features + ["label"], context=path)
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
        assert_file_exists(test_csv, "test_csv")
        df_test = pd.read_csv(test_csv)
        df_test = normalize_columns(df_test)
        df_test = patch_winner_column(df_test)
        df_test = df_test.dropna(subset=features + ["odds"])
        assert_columns_exist(
            df_test,
            features + ["odds"],
            context="test set",
        )
        log_info(f"📥 Loaded {len(df_test)} test rows from {test_csv}")
    except Exception as e:
        log_error(f"❌ Failed to prepare test data: {e}")
        return

    # Train & predict
    try:
        model = LogisticRegression(max_iter=1000)
        model.fit(df_train[features], df_train["label"])
        df_test["predicted_prob"] = model.predict_proba(df_test[features])[:, 1]
        log_success("✅ Model trained and predictions made")
        # Save the trained model
        joblib.dump(model, output_model)
        log_success(f"💾 Trained model saved to {output_model}")
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
            df_test, ev_threshold, max_odds, max_margin
        )
        log_success(f"✅ Filtered {len(df_filtered)} value bets")
    except Exception as e:
        log_error(f"❌ Value bet filtering failed: {e}")
        return

    # Write value bets CSV
    df_filtered.to_csv(value_bets_csv, index=False)
    log_success(f"📝 Saved value bets to {value_bets_csv}")

    # Simulate bankroll
    try:
        sim_df, final_bankroll, max_drawdown = simulate_bankroll(
            df_filtered,
            strategy=strategy,
            initial_bankroll=1000.0,
            ev_threshold=0.0,
            odds_cap=100.0,
            cap_fraction=0.05,
        )
        log_info(f"💰 Final bankroll: {final_bankroll:.2f}")
        log_info(f"📉 Max drawdown: {max_drawdown:.2f}")
        # Save bankroll CSV
        Path(bankroll_csv).parent.mkdir(parents=True, exist_ok=True)
        sim_df.to_csv(bankroll_csv, index=False)
        log_success(f"✅ Saved bankroll simulation to {bankroll_csv}")
        # Plot
        plot_path = Path(bankroll_csv).with_suffix(".png")
        generate_bankroll_plot(sim_df["bankroll"], output_path=plot_path)
        log_success(f"🖼️ Saved bankroll plot to {plot_path}")
    except Exception as e:
        log_error(f"❌ Simulation or saving failed: {e}")

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
    train_eval_model(
        train_csvs=_args.train_csvs,
        test_csv=_args.test_csv,
        value_bets_csv=_args.value_bets_csv,
        bankroll_csv=_args.bankroll_csv,
        features=_args.features,
        output_model=_args.output_model,
        ev_threshold=_args.ev_threshold,
        max_odds=_args.max_odds,
        max_margin=_args.max_margin,
        strategy=_args.strategy,
        fixed_stake=_args.fixed_stake,
        overwrite=_args.overwrite,
        dry_run=_args.dry_run,
    )

if __name__ == "__main__":
    main()
