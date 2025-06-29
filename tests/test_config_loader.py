import tempfile
import json
import pytest

from scripts.utils.config_loader import load_config

DEFAULTS = {
    "host": "localhost",
    "port": 8080,
    "nested": {"a": 1, "b": 2},
}


def write_and_load(ext, content):
    with tempfile.NamedTemporaryFile(suffix=ext, mode="w+", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        return load_config(tmp.name, DEFAULTS)


def test_json_merge():
    cfg = write_and_load(
        ".json", json.dumps({"port": 9090, "nested": {"b": 20, "c": 30}})
    )
    assert cfg["host"] == "localhost"
    assert cfg["port"] == 9090
    assert cfg["nested"] == {"a": 1, "b": 20, "c": 30}


def test_yaml_merge():
    yaml_content = """
    port: 7070
    nested:
      b: 99
    """
    cfg = write_and_load(".yaml", yaml_content)
    assert cfg["port"] == 7070
    assert cfg["nested"]["b"] == 99


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("no_such_file.yaml", DEFAULTS)


def test_non_mapping():
    text = "- just\n- a\n- list\n"
    with pytest.raises(ValueError):
        write_and_load(".yml", text)
