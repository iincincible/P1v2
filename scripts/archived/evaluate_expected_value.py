import argparse
import pandas as pd

def calculate_ev(prob, odds):
    return prob * (odds - 1) - (1 - prob)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--prob_col", default="p_model", help="Column name for win probability (default: p_model)")
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    parser.add_argument("--add_best_bet", action="store_true", help="Add best bet side and EV to output")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    if args.prob_col not in df.columns:
        raise ValueError(f"❌ Probability column '{args.prob_col}' not found.")

    # Calculate EV for both players
    df["ev_p1_model"] = calculate_ev(df[args.prob_col], df["odds_player_1"])
    df["ev_p2_model"] = calculate_ev(1 - df[args.prob_col], df["odds_player_2"])

    df["is_value_p1"] = df["ev_p1_model"] > args.ev_threshold
    df["is_value_p2"] = df["ev_p2_model"] > args.ev_threshold

    # Optional: mark side with max EV
    if args.add_best_bet:
        df["best_bet_side"] = df[["ev_p1_model", "ev_p2_model"]].idxmax(axis=1).str.extract(r"ev_(p\d)_model")[0]
        df["max_ev"] = df[["ev_p1_model", "ev_p2_model"]].max(axis=1)

    # Print summary
    v1 = df["is_value_p1"].sum()
    v2 = df["is_value_p2"].sum()
    print(f"🔍 Value bets detected: P1 = {v1}, P2 = {v2}")
    print(f"📊 Avg EV P1: {df['ev_p1_model'].mean():.4f}, P2: {df['ev_p2_model'].mean():.4f}")

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved EV analysis to {args.output_csv}")

if __name__ == "__main__":
    main()
