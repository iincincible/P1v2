import pandas as pd
from pathlib import Path

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import log_info
from scripts.utils.schema import normalize_columns, enforce_schema


def merge_final_ltps(df_matches: pd.DataFrame, df_snaps: pd.DataFrame) -> pd.DataFrame:
    df_matches = normalize_columns(df_matches)
    df_snaps = normalize_columns(df_snaps)
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
    df_matches = pd.read_csv(matches_csv)
    log_info(f"Loaded {len(df_matches)} matches from {matches_csv}")
    df_snaps = pd.read_csv(snapshots_csv)
    log_info(f"Loaded {len(df_snaps)} snapshots from {snapshots_csv}")
    df_merged = merge_final_ltps(df_matches, df_snaps)
    out_path = Path(output_csv)
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_merged.to_csv(out_path, index=False)
        log_info(f"Merged matches written to {out_path}")
