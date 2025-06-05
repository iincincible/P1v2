import argparse
import pandas as pd
import joblib
from pathlib import Path
import os

def compute_ev(df):
    df["ev"] = (df["pred_prob_player_1"] * df["odds_player_1"]) - 1
    return df

def compute_kelly_stake(prob_series, odds_series):
    b = odds_series - 1
    q = 1 - prob_series
    edge = (b * prob_series - q) / b
    return edge.clip(lower=0)

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

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    df = pd.read_csv(args.input_csv)
    df = compute_ev(df)
    original_count = len(df)

    filtered = df[
        (df["ev"] >= args.ev_threshold) &
        (df["odds_player_1"] <= args.max_odds) &
        (df["odds_margin"] <= args.max_margin)
    ].copy()

    if args.filter_model:
        model = joblib.load(args.filter_model)
        filtered = apply_confidence_model(filtered, model)
        if args.min_confidence is not None:
            filtered = filtered[filtered["confidence_score"] >= args.min_confidence]

    filtered["kelly_stake"] = compute_kelly_stake(
        filtered["pred_prob_player_1"],
        filtered["odds_player_1"]
    )

    filtered = filtered.sort_values("ev", ascending=False)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(filtered)} value bets to {args.output_csv}")

if __name__ == "__main__":
    main()
