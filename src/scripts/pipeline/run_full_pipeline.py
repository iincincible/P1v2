import traceback
from pathlib import Path

import joblib
import pandas as pd

from scripts.pipeline.stages import STAGE_FUNCS
from scripts.utils.config import load_config
from scripts.utils.constants import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_MARGIN,
    DEFAULT_MAX_ODDS,
)
from scripts.utils.logger import log_error, log_info, log_success, log_warning


def resolve_stage_paths(label_cfg, working_dir):
    """
    Returns a dict mapping expected file types to resolved paths for a label.
    Follows convention: <working_dir>/<label>_<stage>.csv (unless already specified in config).
    """
    paths = {}
    label = label_cfg["label"]
    all_keys = [
        "snapshots_csv",
        "matches_csv",
        "matches_with_ids_csv",
        "merged_matches_csv",
        "features_csv",
        "predictions_csv",
        "value_bets_csv",
        "simulation_csv",
        "model_file",
    ]
    for key in all_keys:
        if key in label_cfg:
            paths[key] = Path(label_cfg[key])
        elif key.endswith("_csv"):
            base = working_dir / f"{label}_{key.replace('_csv', '')}.csv"
            paths[key] = base
    return paths


def run_pipeline_for_label(
    label_cfg,
    stages,
    working_dir,
    dry_run=False,
    overwrite=False,
    verbose=False,
    json_logs=False,
    only=None,
):
    label = label_cfg["label"]
    log_info(f"\n🏷️  Starting pipeline for label: {label}")
    resolved_paths = resolve_stage_paths(label_cfg, working_dir)
    stage_output_paths = {}
    pipeline_ok = True

    for stage in stages:
        if only and stage not in only:
            continue

        stage_info = STAGE_FUNCS.get(stage)
        if not stage_info:
            log_warning(f"⚠️  Unknown stage '{stage}', skipping.")
            continue

        log_info(f"--- Stage: {stage} ---")
        fn = stage_info["fn"]
        input_keys = stage_info["input_keys"]
        output_key = stage_info["output_key"]
        output_path = resolved_paths.get(output_key)

        if not output_path:
            log_error(
                f"❌ Could not resolve output path for key '{output_key}' in stage '{stage}'."
            )
            pipeline_ok = False
            break

        if not overwrite and not dry_run and output_path.exists():
            log_info(f"Skipping stage '{stage}': output file already exists.")
            stage_output_paths[output_key] = output_path
            continue

        try:
            input_paths = {}
            for k in input_keys:
                input_paths[k] = resolved_paths.get(k) or stage_output_paths.get(k)
                if not input_paths[k]:
                    raise RuntimeError(f"Missing input '{k}' for stage '{stage}'")

            log_info(f"Running {stage} with inputs: {input_paths}")

            # Execute stage
            if dry_run:
                log_info(f"[DRY-RUN] Would write to {output_path}")
                result = None
            elif stage == "predict":
                model = joblib.load(input_paths["model_file"])
                features_df = pd.read_csv(input_paths["features_csv"])
                result = fn(model, features_df)
            elif stage == "detect":
                # Use per-tournament config values, with fallback to constants
                ev_thresh = label_cfg.get("ev_threshold", DEFAULT_EV_THRESHOLD)
                conf_thresh = label_cfg.get(
                    "confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD
                )
                max_odds = label_cfg.get("max_odds", DEFAULT_MAX_ODDS)
                max_margin = label_cfg.get("max_margin", DEFAULT_MAX_MARGIN)

                predictions_df = pd.read_csv(input_paths["predictions_csv"])
                result = fn(
                    predictions_df,
                    ev_threshold=ev_thresh,
                    confidence_threshold=conf_thresh,
                    max_odds=max_odds,
                    max_margin=max_margin,
                )
            else:
                input_dfs = [pd.read_csv(p) for k, p in input_paths.items()]
                result = fn(*input_dfs)

            if result is not None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(output_path, index=False)
                log_success(f"✅ Stage '{stage}' complete. Output: {output_path}")

            stage_output_paths[output_key] = output_path

        except Exception as e:
            log_error(f"❌ Stage '{stage}' failed for {label}: {e}")
            if verbose:
                traceback.print_exc()
            pipeline_ok = False
            break

    if pipeline_ok:
        log_success(f"🎉 Pipeline finished successfully for label: {label}")
    else:
        log_error(f"💔 Pipeline failed for label: {label}")


def main(
    config="configs/pipeline_run.yaml",
    only=None,
    batch=False,
    dry_run=False,
    overwrite=False,
    verbose=False,
    json_logs=False,
    working_dir="data/processed",
):
    # This function is now the main entry point called by the unified CLI
    app_cfg = load_config(config)
    stages = app_cfg.get("pipeline", {}).get(
        "stages", ["build", "ids", "merge", "features", "predict", "detect", "simulate"]
    )
    working_dir = Path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    labels_to_run = (
        app_cfg.get("tournaments", []) if batch else [app_cfg.get("pipeline", {})]
    )

    log_info(
        f"Pipeline configured to run for {len(labels_to_run)} label(s). Stages: {stages}"
    )
    if only:
        log_warning(f"Running only a subset of stages: {only}")

    for label_cfg in labels_to_run:
        if not label_cfg.get("label"):
            if not batch:
                log_error("❌ No 'label' found in pipeline config. Exiting.")
            continue

        run_pipeline_for_label(
            label_cfg,
            stages,
            working_dir,
            dry_run,
            overwrite,
            verbose,
            json_logs,
            only=only,
        )
