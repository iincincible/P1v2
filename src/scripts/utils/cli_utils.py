import os
from pathlib import Path
import logging


def add_common_flags(parser):
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing outputs"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Only print what would be done, don't write",
    )


def should_run(output_path, overwrite, dry_run):
    output_path = Path(output_path)
    exists = output_path.exists()
    action = None

    if exists and not overwrite:
        logging.info(f"[SKIP] {output_path} exists and --overwrite not set")
        return False
    if dry_run:
        action = "Would overwrite" if exists else "Would write"
        logging.info(f"[DRY-RUN] {action}: {output_path}")
        return False
    return True


def assert_file_exists(path, desc="file"):
    if not Path(path).exists():
        raise FileNotFoundError(f"❌ Missing required {desc}: {path}")


def assert_columns_exist(df, cols, context=""):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns in {context}: {missing}")
