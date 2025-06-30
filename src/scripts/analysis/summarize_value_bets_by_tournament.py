import argparse
import glob
from pathlib import Path

import pandas as pd

from scripts.utils.decorators import with_logging
from scripts.utils.logger import log_info, log_success, log_warning


def run_summarize_value_bets_by_tournament(
    files: list, dry_run: bool = False
) -> pd.DataFrame:
    """
    Summarize value bets by tournament from match-level summaries.
    """
    rows = []
    for filepath in files:
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            log_warning(f"Skipping {filepath}: {e}")
            continue

        required = {"match_id", "total_profit", "avg_ev", "num_bets"}
        if not required.issubset(df.columns):
            log_warning(f"Skipping {filepath} — missing one of: {required}")
            continue

        tournament = Path(filepath).stem.replace("_value_bets_by_match", "")
        num_matches = len(df)
        total_bets = int(df["num_bets"].sum())
        avg_ev = float(df["avg_ev"].mean())
        win_rate = float(df["any_win"].mean()) if "any_win" in df.columns else None
        total_profit = float(df["total_profit"].sum())
        roi = total_profit / total_bets if total_bets > 0 else None

        rows.append(
            {
                "tournament": tournament,
                "num_matches": num_matches,
                "total_bets": total_bets,
                "avg_ev": avg_ev,
                "win_rate": win_rate,
                "profit": total_profit,
                "roi": roi,
            }
        )

    if not rows:
        raise ValueError("No valid tournament summaries found.")

    df_out = pd.DataFrame(rows).sort_values(by="roi", ascending=False)
    return df_out


@with_logging
def main_cli():
    parser = argparse.ArgumentParser(
        description="Summarize value bets by tournament from match-level summaries."
    )
    parser.add_argument(
        "--input_glob",
        required=True,
        help="Glob pattern for match-level summary CSVs (e.g., 'data/*_by_match.csv').",
    )
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()

    files = glob.glob(args.input_glob)
    if not files:
        raise ValueError(
            f"No match-level summary files found matching: {args.input_glob}"
        )

    df_out = run_summarize_value_bets_by_tournament(files, dry_run=args.dry_run)
    if not args.dry_run:
        df_out.to_csv(args.output_csv, index=False)
        log_success(f"Saved tournament-level summary to {args.output_csv}")

    log_info("\nTop 5 by ROI:")
    top5 = df_out[["tournament", "roi", "profit", "total_bets"]].head(5)
    log_info(top5.to_string(index=False))


if __name__ == "__main__":
    main_cli()
