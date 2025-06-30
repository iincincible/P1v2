import logging

from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO", json_logs: bool = False):
    """
    Set up root logger configuration.
    """
    log_handler = logging.StreamHandler()

    if json_logs:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    log_handler.setFormatter(formatter)

    # Get the root logger and remove existing handlers
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(log_handler)
    root_logger.setLevel(level)


def log_info(message: str) -> None:
    """
    Log an info-level message.
    """
    logger.info(message)


def log_success(message: str) -> None:
    """
    Log a success message prefixed with a checkmark.
    """
    logger.info(f"✅ {message}")


def log_warning(message: str) -> None:
    """
    Log a warning-level message prefixed with a warning sign.
    """
    logger.warning(f"⚠️ {message}")


def log_error(message: str) -> None:
    """
    Log an error-level message prefixed with an error sign.
    """
    logger.error(f"❌ {message}")


def log_dryrun(message: str) -> None:
    """
    Log a dry-run notification at INFO level.
    """
    logger.info(f"[DRY-RUN] {message}")
