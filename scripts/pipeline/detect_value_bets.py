import argparse
import pandas as pd
import joblib
from pathlib import Path
from scripts.utils.betting_math import compute_ev, compute_kelly_stake

def normalize_columns(df):
    if "predicted_prob" not in df.columns and "pred_prob_player_1" in df.columns:
        df["predicted_prob"] = df["pred_prob_player_1"]
    if "odds" not in df.columns and "odds_player_1" in df.columns:
        df["odds"] = df["odds_player_1"]
    if "ev" not in df.columns and "expected_value" in df.columns:
        df["ev"] = df["expected_value"]
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.05)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--max_margin", type=float, default=0.05)
    parser.add_argument("--filter_model", default=None)
    parser.add_argument("--min_confidence", type=float, default=None)
    parser.add_argument("--skip_if_exists", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if Path(args.output_csv).exists() and not args.overwrite:
        print(f"⏭️ Output already exists: {args.output_csv}")
        exit()

    base = pd.read_csv(args.input_csv)
    base = normalize_columns(base)
    base["ev"] = (base["predicted_prob"] * base["odds"]) - 1

    print(f"📊 Starting with {len(base)} rows")

    base = base[base["ev"] >= args.ev_threshold]
    print(f"✅ {len(base)} rows pass EV ≥ {args.ev_threshold}")

    base = base[base["odds"] <= args.max_odds]
    print(f"✅ {len(base)} rows pass odds ≤ {args.max_odds}")

    if "odds_margin" in base.columns:
        base = base[base["odds_margin"] <= args.max_margin]
        print(f"✅ {len(base)} rows pass margin ≤ {args.max_margin}")

    if args.filter_model:
        print(f"🔍 Applying confidence filter: {args.filter_model}")
        model = joblib.load(args.filter_model)
        features = ["predicted_prob", "odds", "ev"]
        base = base.copy()
        base["confidence"] = model.predict_proba(base[features])[:, 1]
        if args.min_confidence:
            before = len(base)
            base = base[base["confidence"] >= args.min_confidence]
            print(f"✅ {len(base)} rows pass confidence ≥ {args.min_confidence} (of {before})")

    if not base.empty:
        base["kelly_stake"] = compute_kelly_stake(base["predicted_prob"], base["odds"])
        base = base.sort_values("ev", ascending=False)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(base)} value bets to {args.output_csv}")
