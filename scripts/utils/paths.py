from pathlib import Path

# === Constants ===
DEFAULT_MODEL_PATH = "modeling/win_model.pkl"
DEFAULT_CONFIG_FILE = "configs/tournaments_2024.yaml"
PROCESSED_DIR = Path("data/processed")
PARSED_DIR = Path("parsed")
SNAPSHOT_DIR = Path("parsed")

def get_pipeline_paths(label: str) -> dict:
    """
    Returns all standardized file paths used in the full pipeline for a given tournament label.
    Example label: 'ausopen_2024_atp'
    """
    return {
        "raw_csv": PROCESSED_DIR / f"{label}_clean_snapshot_matches.csv",
        "ids_csv": PROCESSED_DIR / f"{label}_ids.csv",
        "odds_csv": PROCESSED_DIR / f"{label}_with_odds.csv",
        "features_csv": PROCESSED_DIR / f"{label}_features.csv",
        "predictions_csv": PROCESSED_DIR / f"{label}_predictions.csv",
        "value_csv": PROCESSED_DIR / f"{label}_value_bets.csv",
        "bankroll_csv": PROCESSED_DIR / f"{label}_bankroll.csv",
        "snapshot_csv": SNAPSHOT_DIR / f"betfair_{label}_snapshots.csv",
        "summary_png": PROCESSED_DIR / f"{label}_bankroll.png",
    }

def get_snapshot_csv_path(label: str) -> str:
    """
    Shortcut for snapshot file location.
    """
    return str(SNAPSHOT_DIR / f"betfair_{label}_snapshots.csv")
