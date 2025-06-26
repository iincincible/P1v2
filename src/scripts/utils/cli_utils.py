import functools
import sys
import logging
from pathlib import Path
from contextlib import contextmanager

from .errors import ValidationError


def add_common_flags(parser):
    """
    For scripts that take Betfair snapshots and/or results.
    """
    parser.add_argument(
        "--snapshots",
        type=str,
        default=None,
        help="Path to Betfair snapshots CSV (optional).",
    )
    parser.add_argument(
        "--results",
        type=str,
        default=None,
        help="Path to match results CSV (optional).",
    )


def assert_file_exists(path: str) -> None:
    """
    Raise FileNotFoundError if the given path does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required file not found: {p}")


@contextmanager
def output_file_guard(path: Path, overwrite: bool = False):
    """
    Ensure parent dirs exist; enforce overwrite policy.
    Yields a Path that you can pass straight into pandas.to_csv().
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    yield p


def guarded_run(output_arg: str):
    """
    Decorator for entry-point `run()` functions. Handles:
      - parsing args & returning (args, df)
      - central logging setup
      - --dry-run / --overwrite flags
      - writing via output_file_guard
      - exit codes: 0=ok, 2=validation error, 1=unexpected
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper():
            args, df = func()
            logger = logging.getLogger(__name__)

            if getattr(args, "dry_run", False):
                logger.info("Dry run mode: exiting before write.")
                sys.exit(0)

            out_path = getattr(args, output_arg)
            try:
                with output_file_guard(
                    out_path, overwrite=getattr(args, "overwrite", False)
                ) as fp:
                    # Pandas accepts a Path here
                    df.to_csv(fp, index=False)
                logger.info("Wrote output to %s", fp)
                sys.exit(0)

            except ValidationError as ve:
                logger.error("Validation error: %s", ve)
                sys.exit(2)

            except Exception:
                logger.exception("Unexpected failure")
                sys.exit(1)

        return wrapper

    return decorator
