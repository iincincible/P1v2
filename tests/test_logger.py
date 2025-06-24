import logging

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)


def test_log_helpers(caplog):
    caplog.set_level(logging.INFO)

    log_info("just info")
    log_success("it worked")
    log_warning("be careful")
    log_error("something broke")
    log_dryrun("dry run here")

    records = caplog.records
    messages = [rec.message for rec in records]

    # log_info: plain message
    assert "just info" in messages[0]

    # log_success: ✅ prefix
    assert messages[1].startswith("✅ it worked")

    # log_warning: WARNING level and ⚠️ prefix
    warn_records = [r for r in records if r.levelno == logging.WARNING]
    assert any("⚠️ be careful" in r.message for r in warn_records)

    # log_error: ERROR level and ❌ prefix
    err_records = [r for r in records if r.levelno == logging.ERROR]
    assert any("❌ something broke" in r.message for r in err_records)

    # log_dryrun: [DRY-RUN] prefix
    assert any(rec.message.startswith("[DRY-RUN] dry run here") for rec in records)
