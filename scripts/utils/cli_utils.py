from pathlib import Path
import pandas as pd
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.logger import log_success


def load_csv_normalized(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_columns(df)


def save_csv(df: pd.DataFrame, output_path: str, verbose=True):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    if verbose:
        log_success(f"✅ Saved to {output_path}")


def should_run(output_csv: str, overwrite: bool, dry_run: bool) -> bool:
    if dry_run:
        log_success(f"🧪 Dry run: would write to {output_csv}")
        return False
    if not overwrite and Path(output_csv).exists():
        log_success(f"⏭️ Output already exists: {output_csv}")
        return False
    return True


def assert_columns_exist(df: pd.DataFrame, required: list[str], context: str = ""):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns {missing} in {context or 'dataframe'}")


def assert_file_exists(path: str, label: str = ""):
    if not Path(path).exists():
        raise FileNotFoundError(f"❌ Required file missing: {label or path}")


def add_common_flags(parser):
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")
    parser.add_argument("--dry_run", action="store_true", help="Show actions without writing files")
    return parser

def merge_with_defaults(item: dict, defaults: dict) -> dict:
    """
    Recursively merges a single config dict with a defaults dict.
    Values in `item` override those in `defaults`.
    """
    merged = defaults.copy()
    for k, v in item.items():
        if isinstance(v, dict) and isinstance(defaults.get(k), dict):
            merged[k] = merge_with_defaults(v, defaults[k])
        else:
            merged[k] = v
    return merged
