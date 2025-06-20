import logging


def log_info(msg):
    logging.info(msg)


def log_success(msg):
    logging.info(f"✅ {msg}")


def log_warning(msg):
    logging.warning(f"⚠️ {msg}")


def log_error(msg):
    logging.error(f"❌ {msg}")


def log_dryrun(msg):
    logging.info(f"[DRY-RUN] {msg}")
