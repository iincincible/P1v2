import argparse
import pandas as pd
from scripts.utils.cli_utils import assert_file_exists, save_csv
from scripts.utils.betting_math import compute_ev

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.2)
    parser.add_argument("--confidence_threshold", type=float, default=0.4)
    parser.add_argument("--max_odds", type=float, default=None)
    parser.add_argument("--max_margin", type=float, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    assert_file_exists(args.input_csv, "predictions file")

    df = pd.read_csv(args.input_csv)
    if "expected_value" not in df.columns:
        df["expected_value"] = compute_ev(
            df["predicted_prob"], df["odds"], df.get("implied_prob", None)
        )

    base = df.copy()

    # Apply filters
    base = base[base["expected_value"] >= args.ev_threshold]
    if args.confidence_threshold:
        base = base[base["confidence_score"] >= args.confidence_threshold]
    if args.max_odds:
        base = base[base["odds"] <= args.max_odds]
    if args.max_margin:
        base = base[base["odds_margin"] <= args.max_margin]

    if base.empty:
        print("⚠️ No value bets after filtering.")
    else:
        # Assign winner label if actual_winner exists
        if "actual_winner" in base.columns:
            base["winner"] = (base["actual_winner"] == base["player_1"]).astype(int)
        base.to_csv(args.output_csv, index=False)
        print(f"✅ Saved {len(base)} value bets to {args.output_csv}")

if __name__ == "__main__":
    main()
