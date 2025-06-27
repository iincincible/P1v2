import pandas as pd
import glob
from pathlib import Path
from scripts.utils.cli_utils import cli_entrypoint
from scripts.utils.logger import log_info, log_success, log_warning, setup_logging


@cli_entrypoint
def main(
    input_glob: str,
    output_csv: str,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Summarize value bets by tournament from match-level summaries.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = glob.glob(input_glob)
    if not files:
        raise ValueError(f"No match-level summary files found matching: {input_glob}")

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
    if not dry_run:
        df_out.to_csv(output_csv, index=False)
        log_success(f"Saved tournament-level summary to {output_csv}")

    log_info("\nTop 5 by ROI:")
    top5 = df_out[["tournament", "roi", "profit", "total_bets"]].head(5)
    log_info(top5.to_string(index=False))
