from pathlib import Path
import pandas as pd
from scripts.utils.normalize_columns import normalize_columns

def load_csv_normalized(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_columns(df)

def save_csv(df: pd.DataFrame, output_path: str, verbose=True):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    if verbose:
        print(f"✅ Saved to {output_path}")

def should_run(output_csv: str, overwrite: bool, dry_run: bool) -> bool:
    """
    Decides whether a script should continue based on --overwrite and --dry_run flags.
    Returns False if dry run or output exists without --overwrite.
    """
    if dry_run:
        print(f"🧪 Dry run: would write to {output_csv}")
        return False
    if not overwrite and Path(output_csv).exists():
        print(f"⏭️ Output already exists: {output_csv}")
        return False
    return True

def assert_columns_exist(df: pd.DataFrame, required: list[str], context: str = ""):
    """
    Raises ValueError if required columns are missing from the dataframe.
    Optionally provide context to identify which file or step failed.
    """
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns {missing} in {context or 'dataframe'}")
