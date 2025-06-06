import argparse
import os
import sys
import pandas as pd
import joblib

# Patch sys.path so we can import from scripts.utils.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.betting_math import compute_ev, compute_kelly_stake
from scripts.utils.normalize_columns import normalize_columns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    parser.add_argument("--max_odds", type=float, default=1000.0)
    parser.add_argument("--max_margin", type=float, default=1.0)
    parser.add_argument("--filter_model", type=str, default=None)
    parser.add_argument("--min_confidence", type=float, default=0.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        raise FileNotFoundError(f"❌ Input file not found: {args.input_csv}")
    if os.path.exists(args.output_csv) and not args.overwrite:
        print(f"⚠️ Skipping {args.output_csv} (already exists)")
        return

    df = pd.read_csv(args.input_csv)
    df = normalize_columns(df)

    # Compute EV if missing
    if "expected_value" not in df.columns:
        try:
            df["expected_value"] = compute_ev(
                df["predicted_prob"],
                df["odds"]
            )
        except Exception:
            raise ValueError("❌ Cannot compute or find 'expected_value'")

    print(f"📊 Starting with {len(df)} rows")
    base = df[
        (df["expected_value"] >= args.ev_threshold)
        & (df["odds"] <= args.max_odds)
        & (df["odds_margin"] <= args.max_margin)
    ]
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
        base["kelly_stake"] = compute_kelly_stake(base["predicted_prob"], base["odds"])
        base.to_csv(args.output_csv, index=False)
        print(f"✅ Saved {len(base)} value bets to {args.output_csv}")


if __name__ == "__main__":
    main()
