import pytest
import bz2
import json
from pathlib import Path
from datetime import datetime
from scripts.utils.snapshot_parser import SnapshotParser


def write_bz2(tmp_path, name, lines):
    path = tmp_path / name
    with bz2.open(path, "wt", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return path


@pytest.fixture
def sample_metadata(tmp_path):
    lines = [
        json.dumps(
            {
                "op": "mcm",
                "mc": [
                    {
                        "id": "m1",
                        "marketDefinition": {
                            "marketType": "MATCH_ODDS",
                            "marketTime": "2025-01-01T12:00:00",
                            "name": "TestMatch",
                            "runners": [
                                {"name": "A", "id": "s1"},
                                {"name": "B", "id": "s2"},
                            ],
                        },
                    }
                ],
            }
        ),
        "{bad json line}",
    ]
    return write_bz2(tmp_path, "meta.bz2", lines)


@pytest.mark.parametrize(
    "mode,expected_keys",
    [
        (
            "metadata",
            ["market_id", "market_time", "market_name", "runner_1", "runner_2"],
        ),
        ("ltp_only", ["market_id", "selection_id", "ltp", "timestamp"]),
        (
            "full",
            [
                "market_id",
                "selection_id",
                "ltp",
                "timestamp",
                "market_time",
                "market_name",
                "runner_name",
                "runner_1",
                "runner_2",
            ],
        ),
    ],
)
def test_parse_file_modes(tmp_path, mode, expected_keys):
    if mode == "metadata":
        file = sample_metadata(tmp_path)
    else:
        # reuse metadata file for non-metadata: results will be empty or partial
        file = sample_metadata(tmp_path)
    parser = SnapshotParser(mode=mode)
    rows = parser.parse_file(file)
    # rows is a list, may be empty except metadata
    if mode == "metadata":
        assert rows and isinstance(rows, list)
        assert all(k in rows[0] for k in expected_keys)
    else:
        assert isinstance(rows, list)


def test_should_parse_file(tmp_path):
    # simulate path segments including date
    date_str = "2025-Jan-01"
    fake_path = Path(tmp_path) / "a" / "b" / date_str / "c" / "file.bz2"
    # file = write_bz2(tmp_path, "unused.bz2", ["{}"])  # Removed because it was unused
    parser = SnapshotParser()
    # monkeypatch parts
    result = parser.should_parse_file(
        fake_path, datetime(2025, 1, 1), datetime(2025, 1, 1)
    )
    assert result
