import pandas as pd
from pathlib import Path
from scripts.builders.core import build_matches_from_snapshots
from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import setup_logging, log_info
from scripts.utils.schema import enforce_schema


@cli_entrypoint
def main(
    snapshots_csv: str,
    output_csv: str,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Build matches from Betfair snapshots and optional results.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    snapshots_path = Path(snapshots_csv)
    if not snapshots_path.exists():
        log_info(f"Snapshots CSV not found: {snapshots_path}")
        raise FileNotFoundError(snapshots_path)

    df_snapshots = pd.read_csv(snapshots_path)
    log_info(f"Loaded {len(df_snapshots)} snapshots from {snapshots_path}")

    # Build matches from snapshots
    matches_df = build_matches_from_snapshots(df_snapshots)

    # Enforce canonical schema for matches
    matches_df = enforce_schema(matches_df, "matches")

    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {output_path}")
        return

    if dry_run:
        log_info(
            "Dry-run mode; would write %d matches to %s", len(matches_df), output_path
        )
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matches_df.to_csv(output_path, index=False)
        log_info("Matches written to %s", output_path)
