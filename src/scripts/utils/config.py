"""
Configuration loading and validation utilities.
"""

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def _merge_with_defaults(config: dict, defaults: dict) -> dict:
    """
    Deep-merge two dicts: values in `config` override `defaults`,
    and nested dicts are merged recursively.
    """
    merged = defaults.copy()
    for key, val in config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = _merge_with_defaults(val, merged[key])
        else:
            merged[key] = val
    return merged


def load_config(config_path: str, defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Load a configuration from a JSON or YAML file, optionally merged with defaults.
    :param config_path: path to a .json, .yaml, or .yml file
    :param defaults: base/default values (optional)
    :return: merged config dict
    """
    p = Path(config_path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with p.open("r") as f:
        if p.suffix in (".yaml", ".yml"):
            cfg = yaml.safe_load(f)
        elif p.suffix == ".json":
            cfg = json.load(f)
        else:
            raise ValueError(f"Unsupported config file type: {p.suffix}")

    if not isinstance(cfg, dict):
        raise ValueError(
            f"Config file must define a mapping at top level: {config_path}"
        )

    if defaults:
        return _merge_with_defaults(cfg, defaults)

    return cfg
