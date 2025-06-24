from pathlib import Path
import logging
from functools import wraps


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


def dry_run_guard(file_args=(), subprocess_args=()):
    """
    Decorator to skip function body if dry_run is True or file exists (without overwrite).
    file_args: list of arg names that are file outputs.
    subprocess_args: list of arg names to log as subprocess calls in dry-run.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            dry_run = kwargs.get("dry_run") or False
            overwrite = kwargs.get("overwrite") or False
            # File check
            for f in file_args:
                p = kwargs.get(f)
                if p is not None and Path(p).exists() and not overwrite:
                    logging.info(f"[SKIP] {p} exists and --overwrite not set")
                    return None
            if dry_run:
                for f in file_args:
                    p = kwargs.get(f)
                    if p:
                        logging.info(f"[DRY-RUN] Would write: {p}")
                for s in subprocess_args:
                    logging.info(f"[DRY-RUN] Would run subprocess: {kwargs.get(s)}")
                return None
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def output_file_guard(output_arg="output_csv"):
    """
    Decorator for main pipeline functions that write output files.
    Handles overwrite, dry_run, and directory creation for one output file.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            output_path = kwargs.get(output_arg)
            dry_run = kwargs.get("dry_run", False)
            overwrite = kwargs.get("overwrite", False)
            if output_path:
                out_path = Path(output_path)
                if out_path.exists() and not overwrite:
                    print(f"[SKIP] {output_path} exists and --overwrite not set")
                    return
                if dry_run:
                    print(f"[DRY-RUN] Would write: {output_path}")
                    return
                out_path.parent.mkdir(parents=True, exist_ok=True)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
