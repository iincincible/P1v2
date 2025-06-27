import pandas as pd
from pathlib import Path
from importlib import import_module

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import getLogger, setup_logging
from scripts.utils.config import load_config

logger = getLogger(__name__)

STAGE_MODULES = {
    "build": "scripts.builders.core",
    "ids": "scripts.pipeline.match_selection_ids",
    "merge": "scripts.pipeline.merge_final_ltps_into_matches",
    "features": "scripts.pipeline.build_odds_features",
    "predict": "scripts.pipeline.predict_win_probs",
    "detect": "scripts.pipeline.detect_value_bets",
    "simulate": "scripts.pipeline.simulate_bankroll_growth",
}


def run_pipeline_stages_for_tournament(
    tour_config,
    stages,
    output_dir,
    dry_run=False,
    overwrite=False,
):
    name = tour_config.label
    logger.info("Processing tournament: %s", name)
    tour_out = Path(output_dir) / name
    tour_out.mkdir(parents=True, exist_ok=True)
    snap_dir = (
        Path(tour_config.snapshots_csv).parent if tour_config.snapshots_csv else None
    )
    if snap_dir and not snap_dir.exists():
        logger.error("Snapshots directory not found: %s", snap_dir)
        return

    context = {}  # Used to pass DataFrames if desired (future proofing)
    for stage in stages:
        module_path = STAGE_MODULES.get(stage)
        if not module_path:
            logger.error("Unknown pipeline stage: %s", stage)
            continue
        module = import_module(module_path)
        stage_fn = getattr(module, "run_stage", None) or getattr(module, "main")
        logger.info("Running stage '%s'", stage)
        try:
            result = stage_fn(
                df=context.get("df"),
                output_path=str(tour_out / f"{stage}.csv"),
                dry_run=dry_run,
                overwrite=overwrite,
            )
        except Exception:
            logger.exception("Stage '%s' failed for %s", stage, name)
            break
        if isinstance(result, pd.DataFrame):
            context["df"] = result

    logger.info("Completed tournament: %s", name)


@cli_entrypoint
def main(
    config_yaml: str,
    output_dir: str,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Run full pipeline for all tournaments in a YAML config.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    app_cfg = load_config(config_yaml)
    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    for tour in app_cfg.tournaments:
        run_pipeline_stages_for_tournament(
            tour,
            stages=app_cfg.pipeline.stages,
            output_dir=output_dir,
            dry_run=dry_run,
            overwrite=overwrite,
        )

    logger.info("Completed all tournaments.")
