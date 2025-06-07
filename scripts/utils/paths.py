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
    base = PROCESSED_DIR
    return {
        "raw_csv": base / f"{label}_clean_snapshot_matches.csv",
        "ids_csv": base / f"{label}_ids.csv",
        "odds_csv": base / f"{label}_with_odds.csv",
        "features_csv": base / f"{label}_features.csv",
        "predictions_csv": base / f"{label}_predictions.csv",
        "value_csv": base / f"{label}_value_bets.csv",
        "bankroll_csv": base / f"{label}_bankroll.csv",
        "snapshot_csv": SNAPSHOT_DIR / f"betfair_{label}_snapshots.csv",
        "summary_png": base / f"{label}_bankroll.png",
    }

def get_snapshot_csv_path(label: str) -> str:
    """
    Shortcut for snapshot file location.
    Used in builder and parser logic.
    """
    return str(SNAPSHOT_DIR / f"betfair_{label}_snapshots.csv")

def ensure_dir(path: str | Path):
    """
    Ensures the parent directory of a path exists.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
