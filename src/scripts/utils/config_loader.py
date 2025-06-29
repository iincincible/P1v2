import json
from pathlib import Path
import yaml

from .config_utils import merge_with_defaults


def load_config(path: str, defaults: dict) -> dict:
    """
    Load a configuration from a JSON or YAML file, merged with defaults.

    :param path: path to a .json, .yaml, or .yml file
    :param defaults: base/default values
    :return: merged config dict
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with p.open() as f:
        if p.suffix in (".yaml", ".yml"):
            cfg = yaml.safe_load(f)
        else:
            cfg = json.load(f)

    if not isinstance(cfg, dict):
        raise ValueError(f"Config file must define a mapping at top level: {path}")

    return merge_with_defaults(cfg, defaults)
