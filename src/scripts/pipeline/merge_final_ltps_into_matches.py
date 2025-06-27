import pandas as pd
from pathlib import Path

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import setup_logging, log_info
from scripts.utils.schema import enforce_schema


def merge_final_ltps(df_matches: pd.DataFrame, df_snaps: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the final LTP (last traded price) from snapshot data into the matches DataFrame.
    Returns a DataFrame with enforced schema.
    """
    final_snaps = (
        df_snaps.sort_values(["match_id", "selection_id", "timestamp"])
        .groupby(["match_id", "selection_id"], as_index=False)
        .last()[["match_id", "selection_id", "ltp"]]
    )

    df_merged = df_matches.merge(
        final_snaps,
        on=["match_id", "selection_id"],
        how="left",
        suffixes=("", "_final"),
    )
    df_merged.rename(columns={"ltp_final": "final_ltp"}, inplace=True)
    return enforce_schema(df_merged, "merged_matches")


@cli_entrypoint
def main(
    matches_csv: str,
    snapshots_csv: str,
    output_csv: str,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Merge final LTPs into matches.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    matches_path = Path(matches_csv)
    snaps_path = Path(snapshots_csv)
    out_path = Path(output_csv)

    if not matches_path.exists():
        raise FileNotFoundError(f"Matches CSV not found: {matches_path}")
    if not snaps_path.exists():
        raise FileNotFoundError(f"Snapshots CSV not found: {snaps_path}")
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    df_matches = pd.read_csv(matches_path)
    log_info(f"Loaded {len(df_matches)} matches from {matches_path}")
    df_snaps = pd.read_csv(snaps_path)
    log_info(f"Loaded {len(df_snaps)} snapshot rows from {snaps_path}")

    df_merged = merge_final_ltps(df_matches, df_snaps)

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_merged.to_csv(out_path, index=False)
        log_info(f"Merged matches written to {out_path}")
