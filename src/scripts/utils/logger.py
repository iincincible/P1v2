import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


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
