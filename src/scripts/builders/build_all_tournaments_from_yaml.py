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
    "simulate": "scripts.builders.simulate_bankroll_growth",
}


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
    Run the full pipeline for all tournaments in a YAML config.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    app_cfg = load_config(config_yaml)
    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    for tour in app_cfg.tournaments:
        name = tour.label
        logger.info("Processing tournament: %s", name)
        tour_out = out_base / name
        tour_out.mkdir(parents=True, exist_ok=True)
        snap_dir = Path(tour.snapshots_csv).parent if tour.snapshots_csv else None
        if snap_dir and not snap_dir.exists():
            logger.error("Snapshots directory not found: %s", snap_dir)
            continue

        # Here you might want to parse snapshots, etc. as per your original logic

        # For each pipeline stage
        context = {}  # Build up as needed
        for stage in app_cfg.pipeline.stages:
            module_path = STAGE_MODULES.get(stage)
            if not module_path:
                logger.error("Unknown pipeline stage: %s", stage)
                continue
            module = import_module(module_path)
            stage_fn = getattr(module, "run_stage", None) or getattr(module, "main")
            # This will need to adapt to your pipeline stage function signatures!
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

    logger.info("Completed all tournaments.")
