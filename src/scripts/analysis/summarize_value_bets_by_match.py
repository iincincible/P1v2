import pandas as pd
import glob
from scripts.utils.normalize_columns import (
    normalize_and_patch_canonical_columns,
    enforce_canonical_columns,
)
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.cli import guarded_run
from scripts.utils.logger import log_info, log_success, log_warning, setup_logging


@guarded_run
def main(
    value_bets_glob: str,
    output_csv: str,
    top_n: int = 10,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Summarize value bets by match across multiple files.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = glob.glob(value_bets_glob)
    if not files:
        raise ValueError(f"No value bet files found matching: {value_bets_glob}")

    all_bets = []
    for filepath in files:
        try:
            df = pd.read_csv(filepath)
            df = normalize_and_patch_canonical_columns(df, context=filepath)
            df = add_ev_and_kelly(df)
            all_bets.append(df)
        except Exception as e:
            log_warning(f"Skipping {filepath}: {e}")

    if not all_bets:
        raise ValueError(
            "No valid value bet files found after normalization and validation."
        )

    combined = pd.concat(all_bets, ignore_index=True)
    enforce_canonical_columns(combined, context="summarize_value_bets_by_match")
    log_info(f"Loaded {len(combined)} total bets across all files.")

    grouped = combined.groupby("match_id").agg(
        num_bets=("expected_value", "count"),
        avg_ev=("expected_value", "mean"),
        max_confidence=("predicted_prob", "max"),
        any_win=("winner", "max"),
        total_staked=("kelly_stake", "sum"),
        total_profit=lambda g: (
            (g["winner"] * (g["odds"] - 1)) - (~g["winner"].astype(bool)) * 1.0
        ).sum(),
    )

    firsts = combined.drop_duplicates("match_id")[
        ["match_id", "player_1", "player_2"]
    ].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()

    if top_n > 0:
        preview = summary.sort_values(by="total_profit", ascending=False).head(top_n)
        log_info("\nTop Matches by Profit:")
        log_info(
            preview[
                [
                    "match_id",
                    "player_1",
                    "player_2",
                    "num_bets",
                    "avg_ev",
                    "total_profit",
                ]
            ].to_string(index=False)
        )

    summary.to_csv(output_csv, index=False)
    log_success(f"Saved match-level summary to {output_csv}")


if __name__ == "__main__":
    main()
