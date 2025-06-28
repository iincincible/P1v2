"""
Configuration loading and validation utilities.
"""

import yaml
from typing import Any, Dict


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file for tournaments/pipeline.
    """
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    # Optional: validate schema here
    return cfg
