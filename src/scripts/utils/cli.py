import functools
import sys
import argparse
from scripts.utils.logger import log_info, log_error


def guarded_run(main_func):
    @functools.wraps(main_func)
    def wrapper(*args, **kwargs):
        parser = argparse.ArgumentParser(description=main_func.__doc__ or "")
        params = main_func.__code__.co_varnames[: main_func.__code__.co_argcount]
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
        # Try to infer parameter types from defaults
        for p in params:
            if p in {"dry_run", "overwrite", "verbose", "json_logs"}:
                continue
            default = main_func.__defaults__ or ()
            idx = list(params).index(p)
            dval = None
            if idx >= len(params) - len(default):
                dval = default[idx - (len(params) - len(default))]
            t = type(dval) if dval is not None else str
            arg_type = bool if t is bool else t
            if t is bool:
                parser.add_argument(
                    f"--{p}", action="store_true", help=f"{p} (bool flag)"
                )
            else:
                parser.add_argument(
                    f"--{p}", required=dval is None, type=arg_type, default=dval
                )
        cli_args = parser.parse_args()
        kwargs = vars(cli_args)
        try:
            main_func(**kwargs)
        except KeyboardInterrupt:
            log_info("Interrupted.")
            sys.exit(130)
        except Exception as e:
            log_error(f"Fatal error: {e}")
            sys.exit(1)

    return wrapper
