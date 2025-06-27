import argparse
import functools
import sys
from typing import Callable
from scripts.utils.logger import setup_logging, log_info, log_error


def cli_entrypoint(main_func: Callable):
    """
    Decorator for CLI entrypoints.
    Adds --dry_run, --overwrite, --verbose, --json_logs.
    Handles argument parsing and basic error handling.
    """

    @functools.wraps(main_func)
    def wrapper():
        parser = argparse.ArgumentParser(description=main_func.__doc__ or "")
        params = main_func.__code__.co_varnames[: main_func.__code__.co_argcount]
        defaults = main_func.__defaults__ or ()
        for idx, param in enumerate(params):
            if param in {"dry_run", "overwrite", "verbose", "json_logs"}:
                continue  # added below
            default_idx = idx - (len(params) - len(defaults))
            if defaults and default_idx >= 0:
                default = defaults[default_idx]
                arg_type = type(default) if default is not None else str
                if isinstance(default, bool):
                    parser.add_argument(
                        f"--{param}", action="store_true", default=default
                    )
                else:
                    parser.add_argument(f"--{param}", type=arg_type, default=default)
            else:
                parser.add_argument(f"--{param}", required=True, type=str)
        # Add common flags
        parser.add_argument(
            "--dry_run", action="store_true", help="Dry run: do not write outputs"
        )
        parser.add_argument(
            "--overwrite", action="store_true", help="Allow overwriting output files"
        )
        parser.add_argument("--verbose", action="store_true", help="Verbose logging")
        parser.add_argument(
            "--json_logs", action="store_true", help="JSON-formatted logs"
        )
        args = parser.parse_args()
        setup_logging(
            level="DEBUG" if args.verbose else "INFO", json_logs=args.json_logs
        )
        try:
            main_func(**vars(args))
        except KeyboardInterrupt:
            log_info("Interrupted.")
            sys.exit(130)
        except Exception as e:
            log_error(f"Fatal error: {e}")
            sys.exit(1)

    return wrapper
