import argparse
import logging
from pathlib import Path

from scripts.builders.build_clean_matches_generic import build_matches
from scripts.utils.cli_utils import add_common_flags, should_run
from scripts.utils.config_utils import load_tournament_configs
from scripts.utils.config_validation import TOURNAMENTS_SCHEMA, config_validator
from scripts.utils.logger import (
    log_dryrun,
    log_error,
    log_info,
    log_success,
)
from scripts.utils.paths import get_pipeline_paths, get_snapshot_csv_path

# Refactor: Add logging config
logging.basicConfig(level=logging.INFO)


def parse_snapshots_if_needed(conf, overwrite: bool, dry_run: bool) -> str:
    label = conf.label
    snapshot_csv = conf.snapshots_csv or get_snapshot_csv_path(label)
    if Path(snapshot_csv).exists() and not overwrite:
        log_info(f"📄 Using existing snapshots: {snapshot_csv}")
        return snapshot_csv

    if dry_run:
        log_dryrun(f"Would generate snapshots for {label} → {snapshot_csv}")
        return snapshot_csv

    # Placeholder: insert call to snapshot parser here if needed
    log_info(f"[SKIP:FAKE] Would parse raw Betfair data to generate {snapshot_csv}")
    return snapshot_csv


@config_validator(TOURNAMENTS_SCHEMA, "config")
def main(args=None):
    parser = argparse.ArgumentParser(
        description="Build raw matches for all tournaments in YAML config."
    )
    parser.add_argument(
        "--config",
        default="configs/tournaments.yaml",
        help="Path to tournaments YAML config",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    if _args.dry_run:
        log_dryrun(f"Would build all tournaments from {_args.config}")

    try:
        configs = load_tournament_configs(_args.config)
    except Exception as e:
        log_error(f"❌ Invalid YAML config {_args.config}: {e}")
        return

    for conf in configs:
        log_info(f"\n🏗️ Building: {conf.label}")
        try:
            snapshot_csv = parse_snapshots_if_needed(
                conf, _args.overwrite, _args.dry_run
            )
            paths = get_pipeline_paths(conf.label)
            output_path = paths["raw_csv"]
            if not should_run(output_path, _args.overwrite, _args.dry_run):
                continue

            build_matches(
                tour=conf.tour,
                tournament=conf.tournament,
                year=conf.year,
                snapshots_csv=snapshot_csv,
                output_csv=str(output_path),
                sackmann_csv=conf.sackmann_csv,
                alias_csv=conf.alias_csv,
                player_stats_csv=conf.player_stats_csv,
                snapshot_only=conf.snapshot_only,
                fuzzy_match=conf.fuzzy_match,
                overwrite=_args.overwrite,
                dry_run=_args.dry_run,
            )
            log_success(f"✅ Finished building {conf.label}")
        except Exception as e:
            log_error(f"⚠️ Skipping {conf.label} due to error: {e}")


if __name__ == "__main__":
    main()
