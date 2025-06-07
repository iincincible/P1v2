import argparse
import os
import sys
import pandas as pd
import joblib

# Patch sys.path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.cli_utils import should_run
from scripts.utils.constants import (
    DEFAULT_EV_THRESHOLD,
    DEFAULT_MAX_ODDS,
    DEFAULT_MAX_MARGIN
)
from scripts.utils.filters import filter_value_bets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--max_margin", type=float, default=DEFAULT_MAX_MARGIN)
    parser.add_argument("--filter_model", type=str, default=None)
    parser.add_argument("--min_confidence", type=float, default=0.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    if not should_run(args.output_csv, args.overwrite, args.dry_run):
        return

    if not os.path.exists(args.input_csv):
        raise FileNotFoundError(f"❌ Input file not found: {args.input_csv}")

    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)
    df = add_ev_and_kelly(df)

    print(f"📊 Starting with {len(df)} rows")

    base = filter_value_bets(df, args.ev_threshold, args.max_odds, args.max_margin)
    print(f"✅ {len(base)} rows pass EV ≥ {args.ev_threshold}")
    print(f"✅ {len(base)} rows pass odds ≤ {args.max_odds}")
    print(f"✅ {len(base)} rows pass margin ≤ {args.max_margin}")

    if args.filter_model and os.path.exists(args.filter_model):
        print(f"🔍 Applying confidence filter: {args.filter_model}")
        model = joblib.load(args.filter_model)
        features = model.feature_names_in_.tolist()
        probs = model.predict_proba(base[features])
        base["confidence_score"] = probs[:, 1]
        base = base[base["confidence_score"] >= args.min_confidence]
        print(f"✅ {len(base)} rows pass confidence ≥ {args.min_confidence} (of {len(probs)})")
    else:
        base["confidence_score"] = 1.0

    if base.empty:
        print("⚠️ No value bets after filtering.")
    else:
        base.to_csv(args.output_csv, index=False)
        print(f"✅ Saved {len(base)} value bets to {args.output_csv}")

if __name__ == "__main__":
    main()
