"""
Custom exception types for pipeline errors.
"""


class PipelineError(Exception):
    """General pipeline exception."""

    pass


class ConfigError(PipelineError):
    """Raised when config is missing or malformed."""

    pass


class SchemaError(PipelineError):
    """Raised when schema validation fails."""

    pass
