from pathlib import Path

from scripts.pipeline.build_odds_features import run_build_odds_features
from scripts.pipeline.detect_value_bets import run_detect_value_bets
from scripts.pipeline.match_selection_ids import run_assign_selection_ids
from scripts.pipeline.merge_final_ltps_into_matches import run_merge_final_ltps
from scripts.pipeline.predict_win_probs import run_predict_win_probs
from scripts.pipeline.simulate_bankroll_growth import run_simulate_bankroll_growth
from scripts.builders.build_clean_matches_generic import build_clean_matches

from scripts.utils.config import load_config
from scripts.utils.logger import log_error, log_info, log_success, log_warning

# Stage function mapping: stage name -> (function, input_keys, output_key)
STAGE_FUNCS = {
    "build": {
        "fn": build_clean_matches,
        "input_keys": ["snapshots_csv"],
        "output_key": "matches_csv",
    },
    "ids": {
        "fn": run_assign_selection_ids,
        "input_keys": ["matches_csv", "snapshots_csv"],
        "output_key": "matches_with_ids_csv",
    },
    "merge": {
        "fn": run_merge_final_ltps,
        "input_keys": ["matches_with_ids_csv", "snapshots_csv"],
        "output_key": "merged_matches_csv",
    },
    "features": {
        "fn": run_build_odds_features,
        "input_keys": ["merged_matches_csv"],
        "output_key": "features_csv",
    },
    "predict": {
        "fn": run_predict_win_probs,
        "input_keys": ["features_csv", "model_file"],
        "output_key": "predictions_csv",
    },
    "detect": {
        "fn": run_detect_value_bets,
        "input_keys": ["predictions_csv"],
        "output_key": "value_bets_csv",
    },
    "simulate": {
        "fn": run_simulate_bankroll_growth,
        "input_keys": ["value_bets_csv"],
        "output_key": "simulation_csv",
    },
}


def resolve_stage_paths(label_cfg, stage, working_dir):
    """
    Returns a dict mapping expected file types to resolved paths for a label and stage.
    Follows convention: <working_dir>/<label>_<stage>.csv (unless already specified in config).
    """
    paths = {}
    label = label_cfg["label"]
    for key in [
        "snapshots_csv",
        "matches_csv",
        "matches_with_ids_csv",
        "merged_matches_csv",
        "features_csv",
        "predictions_csv",
        "value_bets_csv",
        "simulation_csv",
    ]:
        if key in label_cfg:
            paths[key] = Path(label_cfg[key])
        else:
            # default: data/{label}_{stage}.csv
            base = working_dir / f"{label}_{key.replace('_csv', '')}.csv"
            paths[key] = base
    if "model_file" in label_cfg:
        paths["model_file"] = Path(label_cfg["model_file"])
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
    log_info(f"\n🏷️ Pipeline for label: {label}")
    stage_outputs = {}
    paths = resolve_stage_paths(label_cfg, None, working_dir)
    for stage in stages:
        if only and stage not in only:
            continue
        stage_info = STAGE_FUNCS.get(stage)
        if not stage_info:
            log_warning(f"⚠️ Unknown stage '{stage}', skipping.")
            continue

        fn = stage_info["fn"]
        input_keys = stage_info["input_keys"]
        output_key = stage_info["output_key"]
        log_info(f"--- Stage: {stage} ---")
        try:
            # Gather input file paths
            inputs = {}
            for k in input_keys:
                if k in paths:
                    inputs[k] = paths[k]
                elif k in stage_outputs:
                    inputs[k] = stage_outputs[k]
                else:
                    log_error(f"Missing input for {stage}: {k}")
                    raise RuntimeError(f"Missing input for {stage}: {k}")

            # Actually run the stage
            log_info(f"Running {stage} with inputs: {inputs}")
            # Load DataFrames as needed for each stage (here, you may need custom code for each)
            # This assumes the functions are "pure", i.e., input/output DataFrames or paths
            # If your functions require raw file paths instead, adjust accordingly.

            # Example: All use CSV IO for now
            import pandas as pd

            # Handle each stage's IO pattern
            if stage == "build":
                df_snapshots = pd.read_csv(inputs["snapshots_csv"])
                result = fn(df_snapshots)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "ids":
                df_matches = pd.read_csv(inputs["matches_csv"])
                df_snaps = pd.read_csv(inputs["snapshots_csv"])
                result = fn(df_matches, df_snaps)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "merge":
                df_matches = pd.read_csv(inputs["matches_with_ids_csv"])
                df_snaps = pd.read_csv(inputs["snapshots_csv"])
                result = fn(df_matches, df_snaps)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "features":
                df_merged = pd.read_csv(inputs["merged_matches_csv"])
                result = fn(df_merged)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "predict":
                import joblib

                model = joblib.load(inputs["model_file"])
                df_features = pd.read_csv(inputs["features_csv"])
                result = fn(model, df_features)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "detect":
                df_pred = pd.read_csv(inputs["predictions_csv"])
                result = fn(df_pred)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            elif stage == "simulate":
                df_bets = pd.read_csv(inputs["value_bets_csv"])
                result = fn(df_bets)
                output_path = paths[output_key]
                if not dry_run:
                    result.to_csv(output_path, index=False)
                stage_outputs[output_key] = output_path
            else:
                log_warning(f"No handler for stage: {stage}")
                continue

            log_success(f"✅ Stage '{stage}' complete for {label}")
        except Exception as e:
            log_error(f"❌ Stage '{stage}' failed for {label}: {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            break


def main(
    config="configs/tournaments_2024.yaml",
    only=None,
    batch=False,
    dry_run=False,
    overwrite=False,
    verbose=False,
    json_logs=False,
    working_dir="data/processed",
):
    app_cfg = load_config(config)
    stages = app_cfg.get("pipeline", {}).get(
        "stages", ["build", "ids", "merge", "features", "predict", "detect", "simulate"]
    )
    working_dir = Path(working_dir)

    if batch:
        for label_cfg in app_cfg.get("tournaments", []):
            try:
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
            except Exception as e:
                log_error(f"❌ Pipeline failed for {label_cfg.get('label')}: {e}")
                continue
    else:
        label_cfg = app_cfg.get("pipeline", {})
        if not label_cfg.get("label"):
            log_error("❌ No 'label' found in pipeline config defaults.")
            return
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the full tennis value bet pipeline"
    )
    parser.add_argument("--config", default="configs/tournaments_2024.yaml")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    parser.add_argument("--working_dir", default="data/processed")
    args = parser.parse_args()
    main(
        config=args.config,
        only=args.only,
        batch=args.batch,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        verbose=args.verbose,
        json_logs=args.json_logs,
        working_dir=args.working_dir,
    )
