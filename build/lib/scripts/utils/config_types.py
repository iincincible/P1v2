from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TournamentConfig:
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
    player_stats_csv: Optional[str] = None


@dataclass
class PipelineConfig:
    label: Optional[str]
    overwrite: bool = False
    config: str = "configs/tournaments.yaml"
    stages: List[dict] = field(default_factory=list)
