"""
Logger utility for pipeline scripts.
"""

import logging
import sys


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """
    Initialize logging. Optionally as JSON.
    """
    loglevel = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=loglevel,
        format=(
            "%(asctime)s %(levelname)s %(message)s"
            if not json_logs
            else '{"timestamp":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
        ),
    )


def log_info(msg: str) -> None:
    logging.info(msg)


def log_warning(msg: str) -> None:
    logging.warning(msg)


def log_error(msg: str) -> None:
    logging.error(msg)


def log_success(msg: str) -> None:
    logging.info(f"SUCCESS: {msg}")


def log_debug(msg: str) -> None:
    logging.debug(msg)
