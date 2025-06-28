"""
CLI utilities for argument parsing, entrypoints, and logging.
"""

import argparse
from functools import wraps
from typing import Callable


def cli_entrypoint(fn: Callable) -> Callable:
    """
    (Deprecated) Decorator for CLI entrypoints.
    Prefer explicit argparse in your main scripts.
    """

    @wraps(fn)
    def wrapper():
        parser = argparse.ArgumentParser(description=fn.__doc__ or "")
        # It's better to manually define all arguments in scripts now.
        parser.add_argument(
            "--help", action="help", help="Show this help message and exit"
        )
        args, unknown = parser.parse_known_args()
        # Pass args as dict if wanted; here, just call with no args.
        fn()

    return wrapper
