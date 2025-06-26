import sys
import argparse
import functools

from scripts.utils.logger import setup_logging, getLogger


def guarded_run(func):
    """
    Decorator for CLI entry points.

    - Inspects the decorated function’s signature to auto-generate argparse flags.
    - Adds common flags: --dry-run, --overwrite, --verbose, --json-logs.
    - Sets up logging before calling the function.
    - Exits with code 0 on success, 1 on exception.
    """
    logger = getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper():
        # Build parser from function signature & docstring
        parser = argparse.ArgumentParser(description=func.__doc__)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without writing output files",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing output files",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable debug-level logging",
        )
        parser.add_argument(
            "--json-logs",
            action="store_true",
            help="Output logs in JSON format",
        )

        # Inspect positional parameters of `func`
        import inspect

        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name in ("dry_run", "overwrite", "verbose", "json_logs"):
                continue
            # treat all other params as required str args
            parser.add_argument(name, type=str)

        args = parser.parse_args()
        # Configure logging
        level = "DEBUG" if args.verbose else "INFO"
        setup_logging(level=level, json=args.json_logs)

        # Build kwargs for the function
        func_kwargs = {k: v for k, v in vars(args).items() if k in sig.parameters}
        try:
            func(**func_kwargs)
            sys.exit(0)
        except Exception:
            logger.exception("Uncaught exception in %s", func.__name__)
            sys.exit(1)

    return wrapper
