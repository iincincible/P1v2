import argparse
import yaml
import subprocess
from pathlib import Path
import os
import sys

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run
from scripts.utils.paths import get_pipeline_paths
from scripts.utils.constants import DEFAULT_MODEL_PATH, DEFAULT_CONFIG_FILE
from scripts.utils.config_utils import load_yaml_config, merge_with_defaults

PYTHON = sys.executable

STAGE_SCRIPTS = {
    "build": "src/scripts/builders/build_all_tournaments_from_yaml.py",
    "ids": "src/scripts/pipeline/match_selection_ids.py",
    "merge": "src/scripts/pipeline/merge_final_ltps_into_matches.py",
    "features": "src/scripts/pipeline/build_odds_features.py",
    "predict": "src/scripts/pipeline/predict_win_probs.py",
    "detect": "src/scripts/pipeline/detect_value_bets.py",
    "simulate": "src/scripts/pipeline/simulate_bankroll_growth.py",
}

def build_args(stage_name, label, paths, defaults):
    if stage_name == "build":
        args = ["--config", defaults.get("config", DEFAULT_CONFIG_FILE)]
        # Only add --overwrite if explicitly requested
        if defaults.get("overwrite", False):
            args.append("--overwrite")
        return args
    elif stage_name == "ids":
        return [
            "--merged_csv",
            str(paths["raw_csv"]),
            "--snapshots_csv",
            str(paths["snapshot_csv"]),
            "--output_csv",
            str(paths["ids_csv"]),
        ]
    elif stage_name == "merge":
        return [
            "--matches_csv",
            str(paths["ids_csv"]),
            "--snapshots_csv",
            str(paths["snapshot_csv"]),
            "--output_csv",
            str(paths["odds_csv"]),
        ]
    elif stage_name == "features":
        return [
            "--input_csv",
            str(paths["odds_csv"]),
            "--output_csv",
            str(paths["features_csv"]),
        ]
    elif stage_name == "predict":
        return [
            "--model_file",
            DEFAULT_MODEL_PATH,
            "--input_csv",
            str(paths["features_csv"]),
            "--output_csv",
            str(paths["predictions_csv"]),
        ]
    elif stage_name == "detect":
        return [
            "--input_csv",
            str(paths["predictions_csv"]),
            "--output_csv",
            str(paths["value_csv"]),
        ]
    elif stage_name == "simulate":
        return [
            "--value_bets_csv",
            str(paths["value_csv"]),
            "--output_csv",
            str(paths["bankroll_csv"]),
        ]
    else:
        raise ValueError(f"❌ Unknown pipeline stage: {stage_name}")

def run_pipeline_for_label(label, tournament_conf, global_defaults, stages, args):
    paths = get_pipeline_paths(label)
    log_info(f"\n🏷️ Pipeline for label: {label}")
    # Optionally merge config logic here if paths or params are controlled by conf
    for stage in stages:
        name = stage["name"]
        script = STAGE_SCRIPTS.get(name)
        if not script:
            log_warning(f"⚠️ Unknown stage '{name}', skipping.")
            continue
        if args.only and name not in args.only:
            continue
        stage_args = build_args(name, label, paths, global_defaults)
        cmd = [PYTHON, script] + stage_args
        if args.overwrite:
            if "--overwrite" not in cmd:
                cmd.append("--overwrite")
        if args.dry_run:
            cmd.append("--dry_run")
        log_info(f"--- Stage: {name} ---")
        log_info(f"Running: {' '.join(str(a) for a in cmd)}")
        if args.dry_run:
            log_dryrun(f"Would run: {' '.join(str(a) for a in cmd)}")
            continue
        try:
            subprocess.run(
                cmd,
                check=True,
                env={**os.environ, "PYTHONPATH": "."},
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            log_success(f"✅ Stage '{name}' complete for {label}")
        except subprocess.CalledProcessError as e:
            log_error(f"❌ Stage '{name}' failed for {label}")
            log_error(str(e))
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

    raw_config = load_yaml_config(_args.config)
    global_defaults = raw_config.get("defaults", {})
    stages = raw_config.get("stages", [])

    if _args.batch:
        # Batch mode: run for every tournament in referenced tournaments YAML
        tournaments_yaml = global_defaults.get("config", None)
        if not tournaments_yaml:
            log_error(
                "❌ No tournaments config specified in pipeline defaults (no 'config' key)."
            )
            return
        tournaments_config = load_yaml_config(tournaments_yaml)
        tournaments_defaults = tournaments_config.get("defaults", {})
        tournaments = tournaments_config.get("tournaments", [])
        if not tournaments:
            log_error(f"❌ No tournaments found in {tournaments_yaml}")
            return
        for t in tournaments:
            label = t.get("label")
            if not label:
                log_warning("⚠️ Skipping tournament with no label.")
                continue
            tournament_conf = merge_with_defaults(t, tournaments_defaults)
            try:
                run_pipeline_for_label(
                    label, tournament_conf, global_defaults, stages, _args
                )
            except Exception as e:
                log_error(f"❌ Pipeline failed for {label}: {e}")
                continue  # Don't stop batch on error
    else:
        # Single run
        label = global_defaults.get("label")
        if not label:
            log_error("❌ No 'label' found in pipeline config defaults.")
            return
        run_pipeline_for_label(label, global_defaults, global_defaults, stages, _args)

if __name__ == "__main__":
    main()
