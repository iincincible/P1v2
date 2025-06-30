"""
Common decorators for CLI scripts.
"""

import functools

from .logger import setup_logging


def with_logging(func):
    """
    A decorator that automatically sets up logging for a CLI function.
    It assumes the decorated function's argparse setup includes
    --verbose and --json_logs flags.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # The function's own argparse instance will handle parsing.
        # This just sets up logging based on the parsed args.
        import sys

        is_verbose = "--verbose" in sys.argv
        use_json_logs = "--json_logs" in sys.argv

        setup_logging(level="DEBUG" if is_verbose else "INFO", json_logs=use_json_logs)

        return func(*args, **kwargs)

    return wrapper
