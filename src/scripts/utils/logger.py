import logging
import sys
import json


def setup_logging(level="INFO", json_logs=False):
    root = logging.getLogger()
    if root.hasHandlers():
        root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(
        level
        if isinstance(level, int)
        else getattr(logging, level.upper(), logging.INFO)
    )


def getLogger(name=None):
    return logging.getLogger(name)


def log_info(msg, *args, **kwargs):
    logging.getLogger().info(msg, *args, **kwargs)


def log_success(msg, *args, **kwargs):
    logging.getLogger().info(f"✔️ {msg}", *args, **kwargs)


def log_warning(msg, *args, **kwargs):
    logging.getLogger().warning(msg, *args, **kwargs)


def log_error(msg, *args, **kwargs):
    logging.getLogger().error(msg, *args, **kwargs)


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)
