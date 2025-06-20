import os
import logging
import pytest
from pathlib import Path

from scripts.utils.cli_utils import (
    should_run,
    assert_file_exists,
    assert_columns_exist,
)


def test_assert_file_exists(tmp_path):
    # Existing file → no exception
    f = tmp_path / "foo.txt"
    f.write_text("hello")
    assert assert_file_exists(str(f), desc="test") is None

    # Missing file → FileNotFoundError
    with pytest.raises(FileNotFoundError):
        assert_file_exists(str(tmp_path / "bar.txt"), desc="missing")


def test_should_run_nonexistent(tmp_path, caplog):
    out = tmp_path / "out.csv"
    caplog.set_level(logging.INFO)

    # File doesn't exist, no overwrite, no dry_run → should run
    assert should_run(str(out), overwrite=False, dry_run=False)

    # File doesn't exist, dry_run → should not run, log dry-run
    caplog.clear()
    assert not should_run(str(out), overwrite=False, dry_run=True)
    assert any("[DRY-RUN]" in rec.message for rec in caplog.records)


def test_should_run_existing_no_overwrite(tmp_path, caplog):
    f = tmp_path / "exists.txt"
    f.write_text("data")
    caplog.set_level(logging.INFO)

    # File exists, no overwrite, no dry_run → skip
    assert not should_run(str(f), overwrite=False, dry_run=False)
    assert any("skip" in rec.message.lower() for rec in caplog.records)


def test_should_run_existing_overwrite(tmp_path):
    f = tmp_path / "exists2.txt"
    f.write_text("data")

    # File exists, overwrite → should run
    assert should_run(str(f), overwrite=True, dry_run=False)


def test_assert_columns_exist():
    import pandas as pd

    df = pd.DataFrame({"a": [1], "b": [2]})

    # Required columns present → no exception
    assert assert_columns_exist(df, ["a"], context="ctx") is None

    # Missing columns → ValueError
    with pytest.raises(ValueError) as exc:
        assert_columns_exist(df, ["a", "c"], context="ctx")
    assert "Missing columns in ctx" in str(exc.value)
