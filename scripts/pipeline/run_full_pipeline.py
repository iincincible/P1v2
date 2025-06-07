import argparse
import yaml
import subprocess
import os
from pathlib import Path
import pandas as pd

from scripts.utils.paths import get_pipeline_paths, DEFAULT_MODEL_PATH
from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.cli_utils import add_common_flags, merge_with_defaults
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS

# Step script paths
SELECTION_SCRIPT = "scripts/pipeline/match_selection_ids.py"
MERGE_SCRIPT = "scripts/pipeline/merge_final_ltps_into_matches.py"
FEATURE_SCRIPT = "scripts/pipeline/build_odds_features.py"
PREDICT_SCRIPT = "scripts/pipeline/predict_win_probs.py"
VALUE_SCRIPT = "scripts/pipeline/detect_value_bets.py"
SIM_SCRIPT = "scripts/pipeline/simulate_bankroll_growth.py"
SUMMARY_SCRIPT = "scripts/analysis/summarize_value_bets_by_match.py"
LEADERBOARD_SCRIPT = "scripts/analysis/summarize_value_bets_by_tournament.py"
LEADERBOARD_PLOT_SCRIPT = "scripts/analysis/plot_tournament_leaderboard.py"
COMBINED_SIM_SCRIPT = "scripts/pipeline/simulate_all_value_bets.py"

PYTHON = str(Path(".venv/Scripts/python.exe").resolve()) if Path(".venv/Scripts/python.exe").exists() else "python"


def run_subprocess(cmd: list[str], label: str = None, dry_run: bool = False):
    cmd_str = " ".join(str(x) for x in cmd)
    if dry_run:
        log_info(f"🧪 Dry run: would run command → {cmd_str}")
        return
    try:
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
    except subprocess.CalledProcessError as e:
        step = cmd[-2] if len(cmd) >= 2 else str(cmd)
        log_error(f"❌ Pipeline failed{f' for {label}' if label else ''} during step: {step}")
        raise


class PipelineRunner:
    def __init__(self, tournament: dict, skip_existing: bool, dry_run: bool):
        self.tournament = tournament
        self.label = tournament["label"]
        self.model_path = tournament.get("model_path", DEFAULT_MODEL_PATH)
        self.paths = get_pipeline_paths(self.label)
        self.skip_existing = skip_existing
        self.dry_run = dry_run

    def validate_inputs(self):
        required = {
            "snapshots_csv": self.tournament["snapshots_csv"],
            "raw_csv": self.paths["raw_csv"],
            "model_path": self.model_path
        }
        for key, path in required.items():
            if not Path(path).exists():
                raise FileNotFoundError(f"❌ Missing {key}: {path}")

        try:
            df = pd.read_csv(self.paths["raw_csv"], nrows=5)
            if "match_id" not in df.columns:
                raise ValueError(f"❌ match_id missing in {self.paths['raw_csv']}")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to validate raw_csv: {e}")

    def run_step(self, name, script_path, args_list, output_path):
        log_info(f"🔧 Step: {name}")
        if self.skip_existing and Path(output_path).exists():
            log_info(f"⏭️ Skipping {output_path} (already exists)")
            return
        if self.dry_run:
            log_info(f"🧪 Would run: {script_path} → {output_path}")
            return
        run_subprocess([PYTHON, script_path] + args_list, label=self.label)

    def run_all_steps(self):
        self.validate_inputs()
        t = self.tournament
        p = self.paths

        self.run_step("Match selection IDs", SELECTION_SCRIPT, [
            "--merged_csv", str(p["raw_csv"]),
            "--snapshots_csv", t["snapshots_csv"],
            "--output_csv", str(p["ids_csv"]),
            "--overwrite"
        ], p["ids_csv"])

        self.run_step("Merge final LTPs", MERGE_SCRIPT, [
            "--match_csv", str(p["ids_csv"]),
            "--snapshots_csv", t["snapshots_csv"],
            "--output_csv", str(p["odds_csv"]),
            "--overwrite"
        ], p["odds_csv"])

        self.run_step("Build odds features", FEATURE_SCRIPT, [
            "--input_csv", str(p["odds_csv"]),
            "--output_csv", str(p["features_csv"]),
            "--overwrite"
        ], p["features_csv"])

        self.run_step("Predict win probabilities", PREDICT_SCRIPT, [
            "--input_csv", str(p["features_csv"]),
            "--model_path", self.model_path,
            "--output_csv", str(p["predictions_csv"]),
            "--overwrite"
        ], p["predictions_csv"])

        self.run_step("Detect value bets", VALUE_SCRIPT, [
            "--input_csv", str(p["predictions_csv"]),
            "--output_csv", str(p["value_csv"]),
            "--ev_threshold", str(DEFAULT_EV_THRESHOLD),
            "--overwrite"
        ], p["value_csv"])

        self.run_step("Simulate bankroll", SIM_SCRIPT, [
            "--input_csvs", str(p["value_csv"]),
            "--output_csv", str(p["bankroll_csv"]),
            "--strategy", "kelly",
            "--ev_threshold", str(DEFAULT_EV_THRESHOLD),
            "--odds_cap", str(DEFAULT_MAX_ODDS),
            "--overwrite"
        ], p["bankroll_csv"])

        summary_path = Path("data/summary") / f"{self.label}_value_bets_by_match.csv"
        self.run_step("Summarize by match", SUMMARY_SCRIPT, [
            "--value_bets_glob", str(p["value_csv"]),
            "--output_csv", str(summary_path),
            "--overwrite"
        ], summary_path)


def main():
    parser = argparse.ArgumentParser(description="Run full tournament pipeline from config.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--skip_existing", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--generate_leaderboard", action="store_true")
    add_common_flags(parser)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    defaults = config.get("defaults", {})
    tournaments = config.get("tournaments", [])

    for t in tournaments:
        try:
            merged = merge_with_defaults(t, defaults)
            runner = PipelineRunner(merged, args.skip_existing, args.dry_run)
            runner.run_all_steps()
        except Exception as e:
            log_error(f"🛑 Aborting {t.get('label', 'unknown')} — {e}")
            break

    if args.generate_leaderboard:
        leaderboard_csv = "data/summary/tournament_leaderboard.csv"
        leaderboard_png = "data/summary/tournament_leaderboard.png"

        run_subprocess([
            PYTHON, LEADERBOARD_SCRIPT,
            "--input_glob", "data/summary/*_value_bets_by_match.csv",
            "--output_csv", leaderboard_csv,
            "--overwrite"
        ], dry_run=args.dry_run)

        run_subprocess([
            PYTHON, LEADERBOARD_PLOT_SCRIPT,
            "--input_csv", leaderboard_csv,
            "--output_png", leaderboard_png,
            "--sort_by", "roi",
            "--top_n", "25"
        ], dry_run=args.dry_run)

        run_subprocess([
            PYTHON, COMBINED_SIM_SCRIPT,
            "--value_bets_glob", "data/processed/*_value_bets.csv",
            "--output_csv", "data/summary/combined_bankroll.csv",
            "--strategy", "kelly",
            "--ev_threshold", str(DEFAULT_EV_THRESHOLD),
            "--odds_cap", str(DEFAULT_MAX_ODDS),
            "--save_plots",
            "--overwrite"
        ], dry_run=args.dry_run)


if __name__ == "__main__":
    main()
