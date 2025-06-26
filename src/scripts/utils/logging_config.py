import logging
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger

    _JSON_AVAILABLE = True
except ImportError:
    _JSON_AVAILABLE = False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_logs: bool = False,
):
    """
    Configure the root logger:
      - console handler (always)
      - optional file handler
      - optional JSON formatting (requires python-json-logger)
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # remove old handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    # choose formatter
    if json_logs:
        if not _JSON_AVAILABLE:
            raise RuntimeError("python-json-logger is required for json_logs")
        fmt = jsonlogger.JsonFormatter()
    else:
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # console
    ch = logging.StreamHandler()
    ch.setLevel(root.level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # file, if requested
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(root.level)
        fh.setFormatter(fmt)
        root.addHandler(fh)
