import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Import your main pipeline stage APIs
from scripts.builders.core import build_matches_from_snapshots
from scripts.pipeline.match_selection_ids import main as match_ids_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_odds_main
from scripts.pipeline.build_odds_features import main as features_main
from scripts.pipeline.predict_win_probs import main as predict_main
from scripts.pipeline.detect_value_bets import detect_value_bets
from scripts.pipeline.simulate_bankroll_growth import main as simulate_main

from scripts.utils.normalize_columns import CANONICAL_REQUIRED_COLUMNS, assert_required_columns

def make_toy_snapshot_csv(path):
    df = pd.DataFrame({
        "market_id": ["m1"],
        "market_time": ["2023-01-01 12:00:00"],
        "runner_1": ["Alice"],
        "runner_2": ["Bob"],
        "selection_id": [101],
        "ltp": [2.2],
        "timestamp": [12345678],
        "runner_name": ["Alice"],
    })
    df.to_csv(path, index=False)

def make_toy_sackmann_csv(path):
    df = pd.DataFrame({
        "player_1": ["Alice"],
        "player_2": ["Bob"],
        "actual_winner": ["Alice"],
        "score": ["6-3 6-2"],
    })
    df.to_csv(path, index=False)

def test_full_pipeline_e2e(tmp_path):
    # 1. Toy inputs
    snapshot_csv = tmp_path / "snapshots.csv"
    sackmann_csv = tmp_path / "sackmann.csv"
    make_toy_snapshot_csv(snapshot_csv)
    make_toy_sackmann_csv(sackmann_csv)

    # 2. Build matches (builder/core)
    matches_df = build_matches_from_snapshots(
        snapshot_csv=str(snapshot_csv),
        sackmann_csv=str(sackmann_csv),
        alias_csv=None,
        snapshot_only=False,
        fuzzy_match=False,
    )
    # Save for downstream pipeline steps
    matches_csv = tmp_path / "matches.csv"
    matches_df.to_csv(matches_csv, index=False)
    # Assert columns
    for col in ["player_1", "player_2", "match_id", "market_id"]:
        assert col in matches_df.columns

    # 3. Match selection IDs (pipeline)
    ids_csv = tmp_path / "ids.csv"
    match_ids_main({
        "merged_csv": str(matches_csv),
        "snapshots_csv": str(snapshot_csv),
        "output_csv": str(ids_csv),
        "overwrite": True,
        "dry_run": False,
    })
    assert ids_csv.exists()

    # 4. Merge odds (pipeline)
    odds_csv = tmp_path / "odds.csv"
    merge_odds_main({
        "matches_csv": str(ids_csv),
        "snapshots_csv": str(snapshot_csv),
        "output_csv": str(odds_csv),
        "overwrite": True,
        "dry_run": False,
    })
    assert odds_csv.exists()

    # 5. Build features
    features_csv = tmp_path / "features.csv"
    features_main({
        "input_csv": str(odds_csv),
        "output_csv": str(features_csv),
        "overwrite": True,
        "dry_run": False,
    })
    assert features_csv.exists()

    # 6. Predict win probs (assume you have a dummy model, or skip if not)
    predictions_csv = tmp_path / "predictions.csv"
    # For the test, if you don't have a model, create a dummy CSV:
    pred_df = pd.read_csv(features_csv)
    pred_df["predicted_prob"] = 0.75  # Dummy value
    pred_df.to_csv(predictions_csv, index=False)

    # 7. Detect value bets
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

    # 8. Simulate bankroll
    bankroll_csv = tmp_path / "bankroll.csv"
    simulate_main({
        "value_bets_csv": str(value_csv),
        "output_csv": str(bankroll_csv),
        "overwrite": True,
        "dry_run": False,
    })
    assert bankroll_csv.exists()
    bankroll_df = pd.read_csv(bankroll_csv)
    assert not bankroll_df.empty

    # Optionally: Check that final bankroll is reasonable
    assert bankroll_df["bankroll"].iloc[-1] >= 0

