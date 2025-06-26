"""
Build all tournaments defined in a YAML config by running the full pipeline:
  1. Validate config
  2. Parse Betfair snapshots
  3. Build matches
  4. Assign selection IDs
  5. Merge results
  6. Generate features
  7. Predict win probabilities
  8. Detect value bets
  9. Simulate bankroll growth
"""

import pandas as pd
from pathlib import Path
from importlib import import_module

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.schema import SchemaManager
from scripts.utils.config import load_and_validate_config
from scripts.utils.snapshot_parser import SnapshotParser

logger = getLogger(__name__)

# Map pipeline stage names to their module paths
STAGE_MODULES = {
    "build": "scripts.builders.core",
    "ids": "scripts.pipeline.match_selection_ids",
    "merge": "scripts.pipeline.merge_final_ltps_into_matches",
    "features": "scripts.pipeline.build_odds_features",
    "predict": "scripts.pipeline.predict_win_probs",
    "detect": "scripts.pipeline.detect_value_bets",
    "simulate": "scripts.builders.simulate_bankroll_growth",
}


@guarded_run
def main(
    config_yaml: str,
    output_dir: str,
    dry_run: bool = False,
    overwrite: bool = False,
):
    """
    Run the full pipeline for all tournaments in a YAML config.

    Args:
        config_yaml: Path to the tournaments YAML file.
        output_dir: Base directory to write pipeline outputs.
        dry_run: If True, simulate without writing any files.
        overwrite: If True, overwrite existing outputs.
    """
    # Load and validate config
    try:
        app_cfg = load_and_validate_config(config_yaml)
    except Exception as e:
        logger.error("Config validation failed: %s", e)
        raise

    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    for tour in app_cfg.tournaments:
        name = tour.name or tour.id
        logger.info("Processing tournament: %s", name)
        tour_out = out_base / name
        tour_out.mkdir(parents=True, exist_ok=True)

        # Step 1: Parse snapshots
        snap_dir = Path(tour.snapshots_dir)
        if not snap_dir.exists():
            logger.error("Snapshots directory not found: %s", snap_dir)
            continue
        parser = SnapshotParser(mode=tour.mode)
        try:
            rows = parser.parse_directory(
                snap_dir,
                start=pd.to_datetime(tour.start_date),
                end=pd.to_datetime(tour.end_date),
            )
        except Exception:
            logger.exception("Failed to parse snapshots for %s", name)
            continue
        if not rows:
            logger.warning("No snapshots found for %s; skipping", name)
            continue
        df = pd.DataFrame(rows)
        SchemaManager.patch_schema(df, "matches")

        context = {"df": df}

        # Execute each pipeline stage
        for stage in app_cfg.pipeline.pipeline:
            module_path = STAGE_MODULES.get(stage)
            if not module_path:
                logger.error("Unknown pipeline stage: %s", stage)
                continue
            module = import_module(module_path)
            stage_fn = getattr(module, "run_stage", None) or getattr(module, "main")
            stage_out = tour_out / f"{stage}.csv"
            logger.info("Running stage '%s' -> %s", stage, stage_out)
            try:
                result = stage_fn(
                    df=context["df"],
                    output_path=str(stage_out),
                    dry_run=dry_run,
                    overwrite=overwrite,
                )
            except Exception:
                logger.exception("Stage '%s' failed for %s", stage, name)
                break

            if isinstance(result, pd.DataFrame):
                context["df"] = result

    logger.info("Completed all tournaments.")


if __name__ == "__main__":
    main()
