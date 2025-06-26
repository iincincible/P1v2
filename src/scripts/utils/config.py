"""
Configuration loader and schema validation for tournament and pipeline YAML files.
"""

import yaml
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError, validator, root_validator
from typing import List, Literal, Optional


class TournamentConfig(BaseModel):
    id: str
    name: Optional[str]
    snapshots_dir: str
    start_date: str
    end_date: str
    mode: Literal["metadata", "ltp_only", "full"] = "full"
    alias_csv: Optional[str] = None
    fuzzy_match: bool = True

    @validator("start_date", "end_date")
    def validate_dates(cls, v):
        # ensure YYYY-MM-DD format
        try:
            from datetime import datetime

            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format for '{v}', expected YYYY-MM-DD")
        return v


class PipelineConfig(BaseModel):
    pipeline: List[
        Literal["build", "ids", "merge", "features", "predict", "detect", "simulate"]
    ] = Field(
        default_factory=lambda: [
            "build",
            "ids",
            "merge",
            "features",
            "predict",
            "detect",
            "simulate",
        ]
    )


class AppConfig(BaseModel):
    tournaments: List[TournamentConfig]
    pipeline: PipelineConfig

    @root_validator(pre=True)
    def unwrap_pipeline(cls, values):
        # allow pipeline as list or under a pipeline key
        if "pipeline" in values and not isinstance(values["pipeline"], dict):
            values["pipeline"] = {"pipeline": values["pipeline"]}
        return values


def load_and_validate_config(path: str) -> AppConfig:
    """
    Load a YAML config file and validate it against the Pydantic models.

    Raises ValidationError if config is invalid.
    """
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(cfg_path.read_text())
    try:
        app_cfg = AppConfig(**raw)
    except ValidationError as e:
        # rethrow with clearer message
        raise ValidationError(f"Invalid configuration in {path}: {e}")
    return app_cfg
