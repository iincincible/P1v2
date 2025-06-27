"""
Unified configuration loader and schema validation.
All config (pipeline/tournament) uses Pydantic models.
"""

import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError


class TournamentConfig(BaseModel):
    label: str
    tour: str
    tournament: str
    year: int
    snapshots_csv: Optional[str] = None
    sackmann_csv: Optional[str] = None
    alias_csv: Optional[str] = None
    fuzzy_match: bool = False
    snapshot_only: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PipelineConfig(BaseModel):
    label: Optional[str]
    overwrite: bool = False
    config: str = "configs/tournaments.yaml"
    stages: List[str] = Field(
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


def load_config(path: str) -> AppConfig:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # Support both {tournaments: [], pipeline: {}} and pipeline as a list
    if "pipeline" in raw and not isinstance(raw["pipeline"], dict):
        raw["pipeline"] = {"stages": raw["pipeline"]}
    try:
        return AppConfig(**raw)
    except ValidationError as e:
        raise ValueError(f"Invalid config {path}:\n{e}")
