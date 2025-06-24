import pandas as pd

from scripts.pipeline.detect_value_bets import detect_value_bets


def make_toy_input_csv(tmpdir, filename):
    # Create a toy CSV with the right columns
    df = pd.DataFrame(
        {
            "player_1": ["Alice", "Bob", "Charlie"],
            "player_2": ["Xena", "Yves", "Zane"],
            "predicted_prob": [0.7, 0.5, 0.2],
            "odds": [2.1, 1.9, 6.0],
            "expected_value": [
                0.47,
                -0.05,
                0.2,
            ],  # Only Alice and Charlie pass threshold 0.2
        }
    )
    path = tmpdir / filename
    df.to_csv(path, index=False)
    return path


def test_detect_value_bets_end_to_end(tmp_path):
    # Arrange
    input_csv = make_toy_input_csv(tmp_path, "toy_predictions.csv")
    output_csv = tmp_path / "toy_value_bets.csv"

    # Act
    detect_value_bets(
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        ev_threshold=0.2,
        confidence_threshold=0.0,  # Let all through on confidence
        max_odds=10,
        max_margin=1.0,
        overwrite=True,
        dry_run=False,
    )

    # Assert
    assert output_csv.exists()
    df = pd.read_csv(output_csv)
    # Should include Alice and Charlie only
    assert set(df["player_1"]) == {"Alice", "Charlie"}
    assert all(df["expected_value"] >= 0.2)


def test_detect_value_bets_dry_run(tmp_path):
    input_csv = make_toy_input_csv(tmp_path, "toy_predictions.csv")
    output_csv = tmp_path / "toy_value_bets.csv"

    # Should not write output in dry_run
    detect_value_bets(
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        ev_threshold=0.2,
        confidence_threshold=0.0,
        max_odds=10,
        max_margin=1.0,
        overwrite=True,
        dry_run=True,
    )
    assert not output_csv.exists()


def test_detect_value_bets_overwrite(tmp_path):
    input_csv = make_toy_input_csv(tmp_path, "toy_predictions.csv")
    output_csv = tmp_path / "toy_value_bets.csv"

    # First write
    detect_value_bets(
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        ev_threshold=0.2,
        confidence_threshold=0.0,
        max_odds=10,
        max_margin=1.0,
        overwrite=True,
        dry_run=False,
    )
    assert output_csv.exists()
    # Now call again with overwrite=False: should skip/leave file unchanged
    mtime_before = output_csv.stat().st_mtime
    detect_value_bets(
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        ev_threshold=0.2,
        confidence_threshold=0.0,
        max_odds=10,
        max_margin=1.0,
        overwrite=False,
        dry_run=False,
    )
    mtime_after = output_csv.stat().st_mtime
    assert mtime_before == mtime_after  # File not touched if not overwrite
