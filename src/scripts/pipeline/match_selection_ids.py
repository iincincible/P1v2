import pandas as pd
from pathlib import Path
from scripts.utils.logger import log_info, log_warning
from scripts.utils.schema import normalize_columns, enforce_schema
from scripts.utils.selection import (
    build_market_runner_map,
    match_player_to_selection_id,
)


def run_assign_selection_ids(
    df_matches: pd.DataFrame,
    df_snaps: pd.DataFrame,
    max_missing_frac: float = 0.1,
    drop_missing_rows: bool = False,
    ignore_missing: bool = False,
) -> pd.DataFrame:
    """
    Assigns Betfair selection IDs to matches based on snapshot data.
    """
    df_matches = normalize_columns(df_matches)
    df_snaps = normalize_columns(df_snaps)
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


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Assign Betfair selection IDs to matches"
    )
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--max_missing_frac", type=float, default=0.1)
    parser.add_argument("--drop_missing_rows", action="store_true")
    parser.add_argument("--ignore_missing", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    df_matches = pd.read_csv(args.merged_csv)
    log_info(f"Loaded {len(df_matches)} matches from {args.merged_csv}")
    df_snaps = pd.read_csv(args.snapshots_csv)
    log_info(f"Loaded {len(df_snaps)} snapshots from {args.snapshots_csv}")
    df_out = run_assign_selection_ids(
        df_matches,
        df_snaps,
        max_missing_frac=args.max_missing_frac,
        drop_missing_rows=args.drop_missing_rows,
        ignore_missing=args.ignore_missing,
    )
    out_path = Path(args.output_csv)
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Saved selection IDs to {out_path}")


if __name__ == "__main__":
    main_cli()
