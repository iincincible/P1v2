import argparse
import pandas as pd
import glob
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import add_common_flags, should_run, assert_file_exists


def main():
    parser = argparse.ArgumentParser(description="Summarize value bets by tournament.")
    parser.add_argument("--input_glob", required=True, help="Glob pattern for *_value_bets_by_match.csv")
    parser.add_argument("--output_csv", required=True, help="Output CSV for tournament summary")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)
    files = glob.glob(args.input_glob)

    if not files:
        raise ValueError(f"❌ No match-level summary files found matching: {args.input_glob}")
    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    rows = []
    for f in files:
        try:
            assert_file_exists(f, "match_summary_csv")
            df = pd.read_csv(f)
            required_cols = {"match_id", "total_profit", "avg_ev", "num_bets"}
            if not required_cols.issubset(df.columns):
                log_warning(f"⚠️ Skipping {f} — missing one of: {required_cols}")
                continue

            tournament = Path(f).stem.replace("_value_bets_by_match", "")
            num_matches = len(df)
            total_bets = df["num_bets"].sum()
            avg_ev = df["avg_ev"].mean()
            win_rate = df["any_win"].mean() if "any_win" in df.columns else None
            total_profit = df["total_profit"].sum()
            roi = total_profit / total_bets if total_bets > 0 else None

            rows.append({
                "tournament": tournament,
                "num_matches": num_matches,
                "total_bets": total_bets,
                "avg_ev": avg_ev,
                "win_rate": win_rate,
                "profit": total_profit,
                "roi": roi,
            })
        except Exception as e:
            log_warning(f"⚠️ Skipping {f}: {e}")

    if not rows:
        raise ValueError("❌ No valid tournament summaries found.")

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values(by="roi", ascending=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_path, index=False)
    log_success(f"✅ Saved tournament-level summary to {output_path}")

    log_info("\n📊 Top 5 by ROI:")
    log_info(df_out[["tournament", "roi", "profit", "total_bets"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
