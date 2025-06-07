import argparse
import pandas as pd
import os
import glob
from pathlib import Path

from scripts.utils.cli_utils import assert_file_exists
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.logger import log_info, log_success, log_warning

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for *_value_bets.csv files")
    parser.add_argument("--output_csv", required=True, help="Path to save grouped match summary")
    parser.add_argument("--top_n", type=int, default=10, help="Print top-N matches by profit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError("❌ No value bet files found.")

    all_bets = []
    for file in files:
        try:
            assert_file_exists(file, "value_bets_csv")
            df = pd.read_csv(file)
            df = normalize_columns(df)

            if "match_id" not in df.columns:
                log_warning(f"⚠️ Skipping {file} — missing 'match_id'")
                continue

            if "winner" not in df.columns:
                if "actual_winner" in df.columns and "player_1" in df.columns:
                    df["winner"] = (
                        df["actual_winner"].str.strip().str.lower() ==
                        df["player_1"].str.strip().str.lower()
                    ).astype(int)
                    log_info(f"🩹 Patched 'winner' from actual_winner in {file}")
                else:
                    log_warning(f"⚠️ Skipping {file} — cannot derive 'winner'")
                    continue

            if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
                df["confidence_score"] = df["predicted_prob"]

            if "kelly_stake" not in df.columns:
                df["kelly_stake"] = 1.0

            all_bets.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {file}: {e}")

    if not all_bets:
        raise ValueError("❌ No valid value bet files found.")

    df = pd.concat(all_bets, ignore_index=True)

    grouped = df.groupby("match_id").agg(
        num_bets=("expected_value", "count"),
        avg_ev=("expected_value", "mean"),
        max_confidence=("confidence_score", "max"),
        any_win=("winner", "max"),
        total_staked=("kelly_stake", "sum"),
        total_profit=(lambda g: ((g["winner"] * (g["odds"] - 1)) - (~g["winner"].astype(bool)) * 1.0).sum())
    )

    firsts = df.drop_duplicates("match_id")[["match_id", "player_1", "player_2"]].set_index("match_id")
    summary = grouped.join(firsts, on="match_id").reset_index()

    if args.top_n > 0:
        preview = summary.sort_values(by="total_profit", ascending=False).head(args.top_n)
        print("\n📊 Top Matches by Profit:")
        print(preview[["match_id", "player_1", "player_2", "num_bets", "avg_ev", "total_profit"]])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    log_success(f"✅ Saved match-level summary to {args.output_csv}")

if __name__ == "__main__":
    main()
