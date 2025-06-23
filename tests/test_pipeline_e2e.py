import pytest
import pandas as pd
from pathlib import Path

from scripts.builders.core import build_matches_from_snapshots
from scripts.pipeline.match_selection_ids import main as match_ids_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_odds_main
from scripts.pipeline.build_odds_features import main as features_main
from scripts.pipeline.predict_win_probs import main as predict_main
from scripts.pipeline.detect_value_bets import detect_value_bets
from scripts.pipeline.simulate_bankroll_growth import main as simulate_main

from scripts.utils.normalize_columns import CANONICAL_REQUIRED_COLUMNS, assert_required_columns

def make_toy_snapshot_csv(path):
    df = pd.DataFrame([
        {
            "market_id": "m1",
            "market_time": "2023-01-01 12:00:00",
            "runner_1": "Alice",
            "runner_2": "Bob",
            "selection_id": 101,
            "ltp": 2.2,
            "timestamp": 12345678,
            "runner_name": "Alice",
            "odds_player_1": 2.2,
        },
        {
            "market_id": "m1",
            "market_time": "2023-01-01 12:00:00",
            "runner_1": "Alice",
            "runner_2": "Bob",
            "selection_id": 202,
            "ltp": 1.7,
            "timestamp": 12345679,
            "runner_name": "Bob",
            "odds_player_2": 1.7,
        },
    ])
    df.to_csv(path, index=False)

def make_toy_sackmann_csv(path):
    df = pd.DataFrame([
        {
            "winner_name": "Alice",
            "loser_name": "Bob",
            "score": "6-3 6-2",
            "actual_winner": "Alice"
        }
    ])
    df.to_csv(path, index=False)

def test_full_pipeline_e2e(tmp_path):
    snapshot_csv = tmp_path / "snapshots.csv"
    sackmann_csv = tmp_path / "sackmann.csv"
    make_toy_snapshot_csv(snapshot_csv)
    make_toy_sackmann_csv(sackmann_csv)

    matches_df = build_matches_from_snapshots(
        snapshot_csv=str(snapshot_csv),
        sackmann_csv=str(sackmann_csv),
        alias_csv=None,
        snapshot_only=False,
        fuzzy_match=False,
    )
    matches_csv = tmp_path / "matches.csv"
    matches_df.to_csv(matches_csv, index=False)
    for col in ["player_1", "player_2", "match_id", "market_id"]:
        assert col in matches_df.columns

    ids_csv = tmp_path / "ids.csv"
    match_ids_main([
        "--merged_csv", str(matches_csv),
        "--snapshots_csv", str(snapshot_csv),
        "--output_csv", str(ids_csv),
        "--overwrite",
    ])
    assert ids_csv.exists()

    odds_csv = tmp_path / "odds.csv"
    merge_odds_main([
        "--matches_csv", str(ids_csv),
        "--snapshots_csv", str(snapshot_csv),
        "--output_csv", str(odds_csv),
        "--overwrite",
    ])
    assert odds_csv.exists()

    odds_df = pd.read_csv(odds_csv)
    def extract_first_float(val):
        if isinstance(val, (float, int)):
            return val
        if isinstance(val, str) and val.startswith("[") and "," in val:
            try:
                return float(val.strip("[]").split(",")[0])
            except Exception:
                return float('nan')
        try:
            return float(val)
        except Exception:
            return float('nan')
    odds_df["odds"] = odds_df["ltp_player_1"].apply(extract_first_float)
    odds_df.to_csv(odds_csv, index=False)

    features_csv = tmp_path / "features.csv"
    features_main([
        "--input_csv", str(odds_csv),
        "--output_csv", str(features_csv),
        "--overwrite",
    ])
    assert features_csv.exists()

    predictions_csv = tmp_path / "predictions.csv"
    pred_df = pd.read_csv(features_csv)
    pred_df["predicted_prob"] = [0.75] * len(pred_df)
    pred_df["expected_value"] = pred_df["predicted_prob"] * pred_df["odds"] - 1
    # Drop any accidental ground truth columns, in any format
    for col in ["actual_winner", "winner_name"]:
        if col in pred_df.columns:
            pred_df = pred_df.drop(columns=[col])
    pred_df.to_csv(predictions_csv, index=False)

    value_csv = tmp_path / "value_bets.csv"
    detect_value_bets(
        input_csv=str(predictions_csv),
        output_csv=str(value_csv),
        ev_threshold=0.2,
        confidence_threshold=0.0,
        max_odds=10.0,
        max_margin=1.0,
        overwrite=True,
        dry_run=False,
    )
    assert value_csv.exists()
    value_df = pd.read_csv(value_csv)
    assert_required_columns(value_df, CANONICAL_REQUIRED_COLUMNS, context="value bets e2e")

    bankroll_csv = tmp_path / "bankroll.csv"
    simulate_main([
        "--value_bets_csv", str(value_csv),
        "--output_csv", str(bankroll_csv),
        "--overwrite",
    ])
    assert bankroll_csv.exists()
    bankroll_df = pd.read_csv(bankroll_csv)
    assert not bankroll_df.empty

    assert bankroll_df["bankroll"].iloc[-1] >= 0
