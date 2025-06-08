import argparse
import yaml
import subprocess
from pathlib import Path
import os
import sys

from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.cli_utils import add_common_flags, merge_with_defaults, should_run
from scripts.utils.paths import get_pipeline_paths

PYTHON = sys.executable
DEFAULT_CONFIG = "configs/pipeline_run.yaml"

STAGE_SCRIPTS = {
    "build": "scripts/builders/build_all_tournaments_from_yaml.py",
    "ids": "scripts/pipeline/match_selection_ids.py",
    "merge": "scripts/pipeline/merge_final_ltps_into_matches.py",
    "features": "scripts/pipeline/build_odds_features.py",
    "predict": "scripts/pipeline/predict_win_probs.py",
    "detect": "scripts/pipeline/detect_value_bets.py",
    "simulate": "scripts/pipeline/simulate_bankroll_growth.py",
}


def build_args(stage_name, label, paths, defaults):
    if stage_name == "build":
        return [
            "--config", defaults.get("config", "configs/tournaments_2023.yaml"),
            "--overwrite"
        ]
    elif stage_name == "ids":
        return [
            "--merged_csv", str(paths["raw_csv"]),
            "--snapshots_csv", str(paths["snapshot_csv"]),
            "--output_csv", str(paths["ids_csv"]),
        ]
    elif stage_name == "merge":
        return [
            "--matches_csv", str(paths["ids_csv"]),
            "--snapshots_csv", str(paths["snapshot_csv"]),
            "--output_csv", str(paths["odds_csv"]),
        ]
    elif stage_name == "features":
        return [
            "--input_csv", str(paths["odds_csv"]),
            "--output_csv", str(paths["features_csv"]),
        ]
    elif stage_name == "predict":
        return [
            "--model_file", "modeling/win_model.pkl",
            "--input_csv", str(paths["features_csv"]),
            "--output_csv", str(paths["predictions_csv"]),
        ]
    elif stage_name == "detect":
        return [
            "--input_csv", str(paths["predictions_csv"]),
            "--output_csv", str(paths["value_csv"]),
        ]
    elif stage_name == "simulate":
        return [
            "--value_bets_csv", str(paths["value_csv"]),
            "--output_csv", str(paths["bankroll_csv"]),
        ]
    else:
        raise ValueError(f"❌ Unknown pipeline stage: {stage_name}")


def main():
    parser = argparse.ArgumentParser(description="Run full value betting pipeline.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to pipeline YAML config")
    parser.add_argument("--only", nargs="*", help="Optional list of stages to run (e.g., 'predict detect')")
    add_common_flags(parser)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    defaults = raw_config.get("defaults", {})
    stages = raw_config.get("stages", [])

    for stage in stages:
        name = stage["name"]
        label = stage.get("label") or defaults.get("label")
        if not label:
            raise ValueError(f"❌ Missing 'label' in stage: {stage}")

        if args.only and name not in args.only:
            continue

        paths = get_pipeline_paths(label)
        script = STAGE_SCRIPTS.get(name)
        if not script:
            log_warning(f"⚠️ Skipping unknown stage: {name}")
            continue

        output_key = {
            "build": "raw_csv",
            "ids": "ids_csv",
            "merge": "odds_csv",
            "features": "features_csv",
            "predict": "predictions_csv",
            "detect": "value_csv",
            "simulate": "bankroll_csv"
        }.get(name)

        output_path = Path(paths[output_key])
        if output_path and not should_run(
            output_path,
            args.overwrite or defaults.get("overwrite", False),
            args.dry_run or defaults.get("dry_run", False)
        ):
            continue

        cmd = [PYTHON, script] + build_args(name, label, paths, defaults)

        if args.overwrite or defaults.get("overwrite", False):
            cmd.append("--overwrite")
        if args.dry_run or defaults.get("dry_run", False):
            log_info(f"🧪 Dry run: would run {script}")
            log_info("      " + " ".join(cmd))
            continue

        log_info(f"\n🚀 Running: {name} ({label})")
        log_info("      " + " ".join(cmd))
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
        log_success(f"✅ Completed: {name} ({label}) → {output_path}")

if __name__ == "__main__":
    main()
