"""
Module for merging configuration dictionaries with defaults.
"""


def merge_with_defaults(config: dict, defaults: dict) -> dict:
    """
    Deep-merge two dicts: values in `config` override `defaults`,
    and nested dicts are merged recursively.
    """
    merged = defaults.copy()
    for key, val in config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = merge_with_defaults(val, merged[key])
        else:
            merged[key] = val
    return merged
