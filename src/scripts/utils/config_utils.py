import yaml
import copy

def load_yaml_config(path):
    with open(path, "r", encoding="utf-8") as f:  # <--- UTF-8 fix
        return yaml.safe_load(f)

def merge_with_defaults(config, defaults):
    """Recursively merge config dict into defaults dict (deep copy)."""
    merged = copy.deepcopy(defaults)
    for k, v in config.items():
        if isinstance(v, dict) and k in merged:
            merged[k] = merge_with_defaults(v, merged[k])
        else:
            merged[k] = v
    return merged
