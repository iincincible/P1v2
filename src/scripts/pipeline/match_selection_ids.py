import pandas as pd
from pathlib import Path

from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import setup_logging, log_info, log_warning
from scripts.utils.schema import enforce_schema
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)


def assign_selection_ids(
    df_matches: pd.DataFrame,
    df_snaps: pd.DataFrame,
    max_missing_frac: float = 0.1,
    drop_missing_rows: bool = False,
    ignore_missing: bool = False,
) -> pd.DataFrame:
    """
    Assign selection IDs to matches based on snapshot data.
    Returns DataFrame with enforced schema.
    """
    market_map = build_market_runner_map(df_snaps)
    df_matches = df_matches.copy()

    df_matches["selection_id_1"] = df_matches.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_1"]
        ),
        axis=1,
    )
    df_matches["selection_id_2"] = df_matches.apply(
        lambda r: match_player_to_selection_id(
            market_map, r["market_id"], r["player_2"]
        ),
        axis=1,
    )

    total = len(df_matches)
    miss1 = df_matches["selection_id_1"].isna().sum()
    miss2 = df_matches["selection_id_2"].isna().sum()
    frac1 = miss1 / total if total else 0
    frac2 = miss2 / total if total else 0
    if miss1 or miss2:
        log_warning(
            f"Unmatched IDs 1: {miss1} ({frac1:.1%}), IDs 2: {miss2} ({frac2:.1%})"
        )
        if (
            frac1 > max_missing_frac or frac2 > max_missing_frac
        ) and not ignore_missing:
            raise ValueError(
                "Too many unmatched IDs. Use --ignore_missing to override."
            )
    if drop_missing_rows:
        before = total
        df_matches = df_matches.dropna(subset=["selection_id_1", "selection_id_2"])
        log_info(f"Dropped {before - len(df_matches)} rows with missing IDs.")

    return enforce_schema(df_matches, "matches_with_ids")


@cli_entrypoint
def main(
    merged_csv: str,
    snapshots_csv: str,
    output_csv: str,
    max_missing_frac: float = 0.1,
    drop_missing_rows: bool = False,
    ignore_missing: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    CLI entrypoint: Assign selection IDs to matches.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    in_matches = Path(merged_csv)
    in_snaps = Path(snapshots_csv)
    out_path = Path(output_csv)

    if not in_matches.exists():
        raise FileNotFoundError(f"Merged CSV not found: {in_matches}")
    if not in_snaps.exists():
        raise FileNotFoundError(f"Snapshots CSV not found: {in_snaps}")
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    df_matches = pd.read_csv(in_matches)
    log_info(f"Loaded {len(df_matches)} matches from {in_matches}")
    df_snaps = pd.read_csv(in_snaps)
    log_info(f"Loaded {len(df_snaps)} snapshots from {in_snaps}")

    df_out = assign_selection_ids(
        df_matches,
        df_snaps,
        max_missing_frac=max_missing_frac,
        drop_missing_rows=drop_missing_rows,
        ignore_missing=ignore_missing,
    )

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Saved selection IDs to {out_path}")
