import yaml
from scripts.utils.config_types import TournamentConfig, PipelineConfig

def load_tournament_configs(yaml_path) -> list:
    with open(yaml_path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    defaults = d.get("defaults", {})
    configs = []
    for t in d.get("tournaments", []):
        conf = {**defaults, **t}
        configs.append(TournamentConfig(**conf))
    return configs

def load_pipeline_config(yaml_path) -> PipelineConfig:
    with open(yaml_path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return PipelineConfig(
        label=d.get("defaults", {}).get("label"),
        overwrite=d.get("defaults", {}).get("overwrite", False),
        config=d.get("defaults", {}).get("config", "configs/tournaments.yaml"),
        stages=d.get("stages", []),
    )
