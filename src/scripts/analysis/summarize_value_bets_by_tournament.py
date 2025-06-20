import argparse
import pandas as pd
import glob
from pathlib import Path

from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists


def main(args=None):
    parser = argparse.ArgumentParser(description="Summarize value bets by tournament.")
    parser.add_argument(
        "--input_glob",
        required=True,
        help="Glob pattern for *_value_bets_by_match.csv files",
    )
    parser.add_argument(
        "--output_csv",
        required=True,
        help="Output CSV for tournament summary",
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    files = glob.glob(_args.input_glob)
    if not files:
        raise ValueError(
            f"❌ No match-level summary files found matching: {_args.input_glob}"
        )

    # Dry-run: log and exit
    if _args.dry_run:
        log_dryrun(
            f"Would process {len(files)} match-summary files matching '{_args.input_glob}' "
            f"and write tournament summary to {_args.output_csv}"
        )
        return

    output_path = Path(_args.output_csv)
    if not should_run(output_path, _args.overwrite, _args.dry_run):
        return

    rows = []
    for filepath in files:
        try:
            assert_file_exists(filepath, "match_summary_csv")
            df = pd.read_csv(filepath)
        except Exception as e:
            log_warning(f"⚠️ Skipping {filepath}: {e}")
            continue

        required = {"match_id", "total_profit", "avg_ev", "num_bets"}
        if not required.issubset(df.columns):
            log_warning(f"⚠️ Skipping {filepath} — missing one of: {required}")
            continue

        # Derive summary metrics
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
        raise ValueError("❌ No valid tournament summaries found.")

    df_out = pd.DataFrame(rows).sort_values(by="roi", ascending=False)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(output_path, index=False)
        log_success(f"✅ Saved tournament-level summary to {output_path}")
    except Exception as e:
        log_error(f"❌ Failed to save summary to {output_path}: {e}")
        return

    # Log top 5
    log_info("\n📊 Top 5 by ROI:")
    top5 = df_out[["tournament", "roi", "profit", "total_bets"]].head(5)
    log_info(top5.to_string(index=False))


if __name__ == "__main__":
    main()
