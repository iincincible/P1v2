import argparse
import logging
from pathlib import Path

from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.logging_config import setup_logging
from scripts.utils.cli_utils import add_common_flags, guarded_run
from scripts.utils.columns import validate_columns


@guarded_run(output_arg="output_csv")
def run():
    parser = argparse.ArgumentParser(
        description="Build matches from Betfair snapshots and optional results."
    )
    # dry-run & overwrite flags
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate but do not write any output.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output file if present.",
    )

    # logging flags
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG-level logging to console."
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Write a copy of all logs here."
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Emit structured JSON logs (needs python-json-logger).",
    )

    # core inputs & outputs
    parser.add_argument("--tour", required=True, help="Tour slug (e.g. 'atp', 'wta').")
    parser.add_argument(
        "--tournament", required=True, help="Tournament slug (e.g. 'ausopen')."
    )
    parser.add_argument(
        "--year", required=True, type=int, help="Year of the tournament (e.g. 2023)."
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        type=Path,
        help="Path for the resulting matches CSV.",
    )

    add_common_flags(parser)
    args = parser.parse_args()

    # initialize centralized logging
    setup_logging(
        level="DEBUG" if args.verbose else "INFO",
        log_file=args.log_file,
        json_logs=args.json_logs,
    )
    logger = logging.getLogger(__name__)

    # validate any upstream files
    if getattr(args, "snapshots", None):
        args.snapshots = Path(args.snapshots)
        if not args.snapshots.exists():
            logger.error("Snapshots file not found: %s", args.snapshots)
            raise FileNotFoundError(args.snapshots)
    if getattr(args, "results", None):
        args.results = Path(args.results)
        if not args.results.exists():
            logger.error("Results file not found: %s", args.results)
            raise FileNotFoundError(args.results)

    logger.info(
        "Building matches for %s / %s / %d", args.tour, args.tournament, args.year
    )
    df = build_matches_from_snapshots(
        tour=args.tour,
        tournament=args.tournament,
        year=args.year,
        snapshots_path=getattr(args, "snapshots", None),
        results_path=getattr(args, "results", None),
    )

    # enforce canonical schema
    validate_columns(df, "matches")

    return args, df


if __name__ == "__main__":
    run()
