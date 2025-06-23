import logging

# Refactor: Add default config for logging
logging.basicConfig(level=logging.INFO)

def log_info(msg):
    """Logs an info-level message."""
    logging.info(msg)

def log_success(msg):
    """Logs an info-level message with success emoji."""
    logging.info(f"✅ {msg}")

def log_warning(msg):
    """Logs a warning-level message with warning emoji."""
    logging.warning(f"⚠️ {msg}")

def log_error(msg):
    """Logs an error-level message with error emoji."""
    logging.error(f"❌ {msg}")

def log_dryrun(msg):
    """Logs a dry-run info-level message."""
    logging.info(f"[DRY-RUN] {msg}")
