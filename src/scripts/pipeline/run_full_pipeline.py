from scripts.builders.build_all_tournaments_from_yaml import main as build_stage_main
from scripts.pipeline.build_odds_features import main as features_stage_main
from scripts.pipeline.detect_value_bets import main as detect_stage_main
from scripts.pipeline.match_selection_ids import main as ids_stage_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_stage_main
from scripts.pipeline.predict_win_probs import main as predict_stage_main
from scripts.pipeline.simulate_bankroll_growth import main as simulate_stage_main
from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.config import load_config
from scripts.utils.logger import log_error, log_info, log_success, log_warning

STAGE_FUNCS = {
    "build": build_stage_main,
    "ids": ids_stage_main,
    "merge": merge_stage_main,
    "features": features_stage_main,
    "predict": predict_stage_main,
    "detect": detect_stage_main,
    "simulate": simulate_stage_main,
}


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
    """
    Run full value betting pipeline for a tournament or all tournaments.
    """
    app_cfg = load_config(config)
    stages = app_cfg.pipeline.stages

    def run_pipeline_for_label(label, stages):
        log_info(f"\n🏷️ Pipeline for label: {label}")
        for stage in stages:
            fn = STAGE_FUNCS.get(stage)
            if not fn:
                log_warning(f"⚠️ Unknown stage '{stage}', skipping.")
                continue
            if only and stage not in only:
                continue
            log_info(f"--- Stage: {stage} ---")
            try:
                fn()  # You may need to pass args depending on your actual pipeline
                log_success(f"✅ Stage '{stage}' complete for {label}")
            except Exception as e:
                log_error(f"❌ Stage '{stage}' failed for {label}: {e}")
                break

    if batch:
        for conf in app_cfg.tournaments:
            label = conf.label
            try:
                run_pipeline_for_label(label, stages)
            except Exception as e:
                log_error(f"❌ Pipeline failed for {label}: {e}")
                continue
    else:
        label = app_cfg.pipeline.label
        if not label:
            log_error("❌ No 'label' found in pipeline config defaults.")
            return
        run_pipeline_for_label(label, stages)
