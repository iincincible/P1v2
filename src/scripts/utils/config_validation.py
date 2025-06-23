import yaml
from cerberus import Validator

PIPELINE_SCHEMA = {
    "defaults": {"type": "dict", "required": False},
    "stages": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {"type": "string", "required": True},
                "label": {"type": "string", "required": False},
            },
        },
        "required": True,
    },
}

TOURNAMENTS_SCHEMA = {
    "defaults": {"type": "dict", "required": False},
    "tournaments": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "label": {"type": "string", "required": True},
                "tour": {"type": "string", "required": True},
                "tournament": {"type": "string", "required": True},
                "year": {"type": "integer", "required": True},
                "snapshots_csv": {"type": "string", "required": False},  # <-- Added!
                # Add other required keys here...
            },
        },
    },
}

def validate_yaml(yaml_path, schema):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    v = Validator(schema)
    if not v.validate(data):
        raise ValueError(f"Config {yaml_path} is invalid:\n{v.errors}")
    return data

def config_validator(schema, yaml_arg):
    """
    Decorator for validating config YAML before running main.
    Expects the main function to accept the config path as a kwarg.
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            yaml_path = kwargs.get(yaml_arg)
            if yaml_path:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                v = Validator(schema)
                if not v.validate(data):
                    raise ValueError(f"Config {yaml_path} is invalid:\n{v.errors}")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
