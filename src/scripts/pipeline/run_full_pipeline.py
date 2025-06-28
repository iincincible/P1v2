from scripts.pipeline.build_odds_features import main as features_stage_main
from scripts.pipeline.detect_value_bets import main as detect_stage_main
from scripts.pipeline.match_selection_ids import main as ids_stage_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_stage_main
from scripts.pipeline.predict_win_probs import main as predict_stage_main
from scripts.pipeline.simulate_bankroll_growth import main as simulate_stage_main
from scripts.builders.build_clean_matches_generic import main as build_stage_main

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.config import load_config
from scripts.utils.logger import log_error, log_info, log_success, log_warning

# Unified mapping: function references
STAGE_FUNCS = {
    "build": build_stage_main,
    "ids": ids_stage_main,
    "merge": merge_stage_main,
    "features": features_stage_main,
    "predict": predict_stage_main,
    "detect": detect_stage_main,
    "simulate": simulate_stage_main,
}


def run_pipeline_for_label(
    label,
    stages,
    config,
    dry_run=False,
    overwrite=False,
    verbose=False,
    json_logs=False,
    only=None,
):
    log_info(f"\n🏷️ Pipeline for label: {label}")
    for stage in stages:
        if only and stage not in only:
            continue
        fn = STAGE_FUNCS.get(stage)
        if not fn:
            log_warning(f"⚠️ Unknown stage '{stage}', skipping.")
            continue
        log_info(f"--- Stage: {stage} ---")
        try:
            # TODO: pass the correct arguments based on config and stage
            fn()
            log_success(f"✅ Stage '{stage}' complete for {label}")
        except Exception as e:
            log_error(f"❌ Stage '{stage}' failed for {label}: {e}")
            break


@cli_entrypoint
def main(
    config: str = "configs/tournaments_2024.yaml",
    only: list = None,
    batch: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    app_cfg = load_config(config)
    stages = app_cfg.pipeline.stages

    if batch:
        for conf in app_cfg.tournaments:
            label = conf.label
            try:
                run_pipeline_for_label(
                    label,
                    stages,
                    config,
                    dry_run,
                    overwrite,
                    verbose,
                    json_logs,
                    only=only,
                )
            except Exception as e:
                log_error(f"❌ Pipeline failed for {label}: {e}")
                continue
    else:
        label = app_cfg.pipeline.label
        if not label:
            log_error("❌ No 'label' found in pipeline config defaults.")
            return
        run_pipeline_for_label(
            label, stages, config, dry_run, overwrite, verbose, json_logs, only=only
        )
