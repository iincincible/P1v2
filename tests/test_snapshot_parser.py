import bz2
import json

import pytest

from scripts.utils.snapshot_parser import SnapshotParser


def _write_bz2(tmp_path, lines):
    """
    Helper: write a list of JSON-serializable objects as JSON‐lines to a .bz2 file.
    Returns the file path.
    """
    path = tmp_path / "snapshot.bz2"
    with bz2.open(path, "wt", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")
    return str(path)


def test_metadata_mode(tmp_path):
    # One mcm message with marketDefinition and two runners
    msg = {
        "op": "mcm",
        "mc": [
            {
                "id": "MKT1",
                "marketDefinition": {
                    "marketTime": "2025-06-29T12:00:00Z",
                    "name": "Test Market",
                    "runners": [{"name": "Alice"}, {"name": "Bob"}],
                },
            }
        ],
    }
    bz2_file = _write_bz2(tmp_path, [msg])
    parser = SnapshotParser(mode="metadata")
    rows = parser.parse_file(bz2_file)

    assert isinstance(rows, list)
    assert len(rows) == 1
    expected = {
        "market_id": "MKT1",
        "market_time": "2025-06-29T12:00:00Z",
        "market_name": "Test Market",
        "runner_1": "Alice",
        "runner_2": "Bob",
    }
    assert rows[0] == expected


def test_ltp_only_mode(tmp_path):
    # Two runner-change entries: one with ltp, one without
    msg = {
        "op": "mcm",
        "pt": 1234567890,
        "mc": [
            {
                "id": "MKT2",
                "rc": [
                    {"id": 1, "ltp": 2.5},
                    {"id": 2, "tv": 100},  # no ltp → should be skipped
                ],
            }
        ],
    }
    bz2_file = _write_bz2(tmp_path, [msg])
    parser = SnapshotParser(mode="ltp_only")
    rows = parser.parse_file(bz2_file)

    assert isinstance(rows, list)
    # only the one with "ltp" should appear
    assert len(rows) == 1
    assert rows[0] == {
        "market_id": "MKT2",
        "market_time": 1234567890,
        "runner_id": 1,
        "last_traded_price": 2.5,
    }


def test_full_mode(tmp_path):
    # One rc entry with all optional fields present
    msg = {
        "op": "mcm",
        "pt": 222333444,
        "mc": [
            {
                "id": "MKT3",
                "rc": [
                    {
                        "id": 5,
                        "ltp": 1.8,
                        "tv": 2500,
                        "atb": [1.8, 100],
                        "atl": [1.9, 50],
                    }
                ],
            }
        ],
    }
    bz2_file = _write_bz2(tmp_path, [msg])
    parser = SnapshotParser(mode="full")
    rows = parser.parse_file(bz2_file)

    assert isinstance(rows, list)
    assert len(rows) == 1
    expected = {
        "market_id": "MKT3",
        "market_time": 222333444,
        "runner_id": 5,
        "last_traded_price": 1.8,
        "total_matched": 2500,
        "best_available_to_back": [1.8, 100],
        "best_available_to_lay": [1.9, 50],
    }
    assert rows[0] == expected


def test_invalid_mode():
    with pytest.raises(ValueError):
        SnapshotParser(mode="bogus")
