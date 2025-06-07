import argparse
import pandas as pd
import glob
from pathlib import Path

from scripts.utils.logger import log_info, log_success, log_warning

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=True, help="Glob for *_value_bets_by_match.csv")
    parser.add_argument("--output_csv", required=True, help="Output CSV for tournament summary")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    files = glob.glob(args.input_glob)
    if not files:
        raise ValueError("❌ No match-level summary files found.")

    rows = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if "match_id" not in df.columns or "total_profit" not in df.columns:
                log_warning(f"Skipping {f} — missing columns.")
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
            log_warning(f"Skipping {f}: {e}")

    if not rows:
        raise ValueError("❌ No valid tournament summaries found.")

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values(by="roi", ascending=False)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output_csv, index=False)
    log_success(f"Saved tournament-level summary to {args.output_csv}")

    print("\n📊 Top 5 by ROI:")
    print(df_out[["tournament", "roi", "profit", "total_bets"]].head(5))

if __name__ == "__main__":
    main()
