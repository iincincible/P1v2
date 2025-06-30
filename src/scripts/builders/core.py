import pandas as pd

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import log_info, setup_logging
from scripts.utils.schema import enforce_schema


def build_matches_from_snapshots(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    grouped = snapshot_df.groupby(
        ["match_id", "market", "selection"], as_index=False
    ).agg(
        ltp=("price", "last"), volume=("volume", "sum"), timestamp=("timestamp", "max")
    )
    matches_df = enforce_schema(grouped, schema_name="matches")
    return matches_df


@cli_entrypoint
def main(input_path: str, output_path: str, dry_run: bool = False):
    """
    Entry point to build matches from snapshot CSV.
    """
    setup_logging()
    df = pd.read_csv(input_path)
    log_info("Loaded %d snapshots from %s", len(df), input_path)
    matches_df = build_matches_from_snapshots(df)
    if dry_run:
        log_info("Dry-run mode active; no file written.")
    else:
        matches_df.to_csv(output_path, index=False)
        log_info("Matches written to %s", output_path)
