import argparse
import pandas as pd
import joblib
from pathlib import Path

def compute_ev(df):
    df["ev"] = (df["pred_prob_player_1"] * df["odds_player_1"]) - 1
    return df

def apply_confidence_model(df, model):
    features = ["pred_prob_player_1", "odds_player_1", "implied_prob_1", "odds_margin", "ev"]
    X = df[features]
    if X.empty:
        print("⚠️ No EV bets passed base filters — skipping confidence scoring.")
        df["confidence_score"] = []
        return df
    df["confidence_score"] = model.predict_proba(X)[:, 1]
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.05)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--max_margin", type=float, default=0.05)
    parser.add_argument("--filter_model", default=None)
    parser.add_argument("--min_confidence", type=float, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    required = ["odds_player_1", "implied_prob_1", "pred_prob_player_1", "odds_margin"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = compute_ev(df)
    original_count = len(df)

    # Base filters
    filtered = df[
        (df["ev"] >= args.ev_threshold) &
        (df["odds_player_1"] <= args.max_odds) &
        (df["odds_margin"] <= args.max_margin)
    ].copy()

    if filtered.empty:
        print(f"⚠️ No value bets found after EV/odds/margin filters (from {original_count} matches)")
        filtered.to_csv(args.output_csv, index=False)
        print(f"✅ Saved empty output to {args.output_csv}")
        return

    # Optional confidence filter
    if args.filter_model:
        model = joblib.load(args.filter_model)
        filtered = apply_confidence_model(filtered, model)
        if args.min_confidence is not None:
            pre_count = len(filtered)
            filtered = filtered[filtered["confidence_score"] >= args.min_confidence]
            print(f"🎯 Filtered {pre_count - len(filtered)} low-confidence bets")

    print(f"🔍 Found {len(filtered)} value bets out of {original_count} matches")
    filtered = filtered.sort_values("ev", ascending=False)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(args.output_csv, index=False)
    print(f"✅ Saved filtered value bets to {args.output_csv}")

if __name__ == "__main__":
    main()
