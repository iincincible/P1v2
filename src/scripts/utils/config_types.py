"""
Dataclasses and types for configuration.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TournamentConfig:
    label: str
    data_path: str
    year: int
    additional_params: dict = field(default_factory=dict)


@dataclass
class PipelineConfig:
    label: str
    stages: List[str]
    overwrite: bool = False
    dry_run: bool = False
