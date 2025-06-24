import argparse
import logging

# Import main functions for all stages
from scripts.builders.build_all_tournaments_from_yaml import main as build_stage_main
from scripts.pipeline.build_odds_features import main as features_stage_main
from scripts.pipeline.detect_value_bets import main as detect_stage_main
from scripts.pipeline.match_selection_ids import main as ids_stage_main
from scripts.pipeline.merge_final_ltps_into_matches import main as merge_stage_main
from scripts.pipeline.predict_win_probs import main as predict_stage_main
from scripts.pipeline.simulate_bankroll_growth import main as simulate_stage_main
from scripts.utils.cli_utils import add_common_flags
from scripts.utils.config_utils import (
    load_pipeline_config,
    load_tournament_configs,
)
from scripts.utils.config_validation import PIPELINE_SCHEMA, config_validator
from scripts.utils.logger import (
    log_error,
    log_info,
    log_success,
    log_warning,
)
from scripts.utils.paths import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_MODEL_PATH,
    get_pipeline_paths,
)

# Refactor: Added logging config
logging.basicConfig(level=logging.INFO)

STAGE_FUNCS = {
    "build": build_stage_main,
    "ids": ids_stage_main,
    "merge": merge_stage_main,
    "features": features_stage_main,
    "predict": predict_stage_main,
    "detect": detect_stage_main,
    "simulate": simulate_stage_main,
}

# Easy to update/add new stages or custom args
STAGE_ARGS = {
    "build": lambda label, paths, conf, cli: dict(
        config=conf.config, overwrite=cli.overwrite, dry_run=cli.dry_run
    ),
    "ids": lambda label, paths, conf, cli: dict(
        merged_csv=str(paths["raw_csv"]),
        snapshots_csv=str(paths["snapshot_csv"]),
        output_csv=str(paths["ids_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
    "merge": lambda label, paths, conf, cli: dict(
        matches_csv=str(paths["ids_csv"]),
        snapshots_csv=str(paths["snapshot_csv"]),
        output_csv=str(paths["odds_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
    "features": lambda label, paths, conf, cli: dict(
        input_csv=str(paths["odds_csv"]),
        output_csv=str(paths["features_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
    "predict": lambda label, paths, conf, cli: dict(
        model_file=DEFAULT_MODEL_PATH,
        input_csv=str(paths["features_csv"]),
        output_csv=str(paths["predictions_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
    "detect": lambda label, paths, conf, cli: dict(
        input_csv=str(paths["predictions_csv"]),
        output_csv=str(paths["value_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
    "simulate": lambda label, paths, conf, cli: dict(
        value_bets_csv=str(paths["value_csv"]),
        output_csv=str(paths["bankroll_csv"]),
        overwrite=cli.overwrite,
        dry_run=cli.dry_run,
    ),
}


def run_pipeline_for_label(label, pipeline_conf, stages, cli_args):
    paths = get_pipeline_paths(label)
    log_info(f"\n🏷️ Pipeline for label: {label}")
    for stage in stages:
        name = stage["name"]
        fn = STAGE_FUNCS.get(name)
        arg_builder = STAGE_ARGS.get(name)
        if not fn or not arg_builder:
            log_warning(f"⚠️ Unknown stage '{name}', skipping.")
            continue
        if cli_args.only and name not in cli_args.only:
            continue
        log_info(f"--- Stage: {name} ---")
        _args = arg_builder(label, paths, pipeline_conf, cli_args)
        try:
            fn(_args)
            log_success(f"✅ Stage '{name}' complete for {label}")
        except Exception as e:
            log_error(f"❌ Stage '{name}' failed for {label}: {e}")
            break


@config_validator(PIPELINE_SCHEMA, "config")
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
