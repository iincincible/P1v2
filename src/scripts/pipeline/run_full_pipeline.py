import argparse
from pathlib import Path
from types import SimpleNamespace

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags
from scripts.utils.paths import get_pipeline_paths, DEFAULT_MODEL_PATH, DEFAULT_CONFIG_FILE
from scripts.utils.config_utils import load_pipeline_config, load_tournament_configs, merge_with_defaults

# Import main functions for all stages
from scripts.builders.build_all_tournaments_from_yaml import main as build_stage_main
from scripts.pipeline.match_selection_ids import main as ids_stage_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_stage_main
from scripts.pipeline.build_odds_features import main as features_stage_main
from scripts.pipeline.predict_win_probs import main as predict_stage_main
from scripts.pipeline.detect_value_bets import main as detect_stage_main
from scripts.pipeline.simulate_bankroll_growth import main as simulate_stage_main

STAGE_FUNCS = {
    "build": build_stage_main,
    "ids": ids_stage_main,
    "merge": merge_stage_main,
    "features": features_stage_main,
    "predict": predict_stage_main,
    "detect": detect_stage_main,
    "simulate": simulate_stage_main,
}

def build_stage_args(stage_name, label, paths, pipeline_conf, cli_args):
    _args = SimpleNamespace()
    if stage_name == "build":
        _args.config = pipeline_conf.config
    elif stage_name == "ids":
        _args.merged_csv = str(paths["raw_csv"])
        _args.snapshots_csv = str(paths["snapshot_csv"])
        _args.output_csv = str(paths["ids_csv"])
    elif stage_name == "merge":
        _args.matches_csv = str(paths["ids_csv"])
        _args.snapshots_csv = str(paths["snapshot_csv"])
        _args.output_csv = str(paths["odds_csv"])
    elif stage_name == "features":
        _args.input_csv = str(paths["odds_csv"])
        _args.output_csv = str(paths["features_csv"])
    elif stage_name == "predict":
        _args.model_file = DEFAULT_MODEL_PATH
        _args.input_csv = str(paths["features_csv"])
        _args.output_csv = str(paths["predictions_csv"])
    elif stage_name == "detect":
        _args.input_csv = str(paths["predictions_csv"])
        _args.output_csv = str(paths["value_csv"])
    elif stage_name == "simulate":
        _args.value_bets_csv = str(paths["value_csv"])
        _args.output_csv = str(paths["bankroll_csv"])
    else:
        raise ValueError(f"Unknown pipeline stage: {stage_name}")
    _args.overwrite = cli_args.overwrite
    _args.dry_run = cli_args.dry_run
    return _args

def run_pipeline_for_label(label, pipeline_conf, stages, cli_args):
    paths = get_pipeline_paths(label)
    log_info(f"\n🏷️ Pipeline for label: {label}")
    for stage in stages:
        name = stage["name"]
        fn = STAGE_FUNCS.get(name)
        if not fn:
            log_warning(f"⚠️ Unknown stage '{name}', skipping.")
            continue
        if cli_args.only and name not in cli_args.only:
            continue
        log_info(f"--- Stage: {name} ---")
        _args = build_stage_args(name, label, paths, pipeline_conf, cli_args)
        try:
            fn(vars(_args))
            log_success(f"✅ Stage '{name}' complete for {label}")
        except Exception as e:
            log_error(f"❌ Stage '{name}' failed for {label}: {e}")
            break

def main(args=None):
    parser = argparse.ArgumentParser(description="Run full value betting pipeline.")
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG_FILE, help="Path to pipeline YAML config"
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional list of stages to run (e.g., 'predict detect')",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run for ALL tournaments in YAML (batch mode)",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    pipeline_conf = load_pipeline_config(_args.config)
    stages = pipeline_conf.stages

    if _args.batch:
        tournament_configs = load_tournament_configs(pipeline_conf.config)
        for conf in tournament_configs:
            label = conf.label
            try:
                run_pipeline_for_label(label, pipeline_conf, stages, _args)
            except Exception as e:
                log_error(f"❌ Pipeline failed for {label}: {e}")
                continue
    else:
        label = pipeline_conf.label
        if not label:
            log_error("❌ No 'label' found in pipeline config defaults.")
            return
        run_pipeline_for_label(label, pipeline_conf, stages, _args)

if __name__ == "__main__":
    main()
