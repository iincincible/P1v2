import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--max_odds", type=float, default=10.0)
    parser.add_argument("--max_margin", type=float, default=0.15)
    parser.add_argument("--ev_threshold", type=float, default=0.01)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    initial_rows = len(df)

    # Compute implied margin if missing
    if "odds_margin" not in df.columns:
        df["implied_prob_1"] = 1 / df["odds_player_1"]
        df["implied_prob_2"] = 1 / df["odds_player_2"]
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1

    # Compute expected value for each side
    df["ev_player_1"] = df["pred_prob_player_1"] * (df["odds_player_1"] - 1) - (1 - df["pred_prob_player_1"])
    df["ev_player_2"] = (1 - df["pred_prob_player_1"]) * (df["odds_player_2"] - 1) - df["pred_prob_player_1"]

    # Flatten both sides into single-row value bets
    bets = []

    for i, row in df.iterrows():
        if row["ev_player_1"] > args.ev_threshold and row["odds_player_1"] <= args.max_odds and row["odds_margin"] <= args.max_margin:
            bets.append({
                "player": row["player_1"],
                "predicted_prob": row["pred_prob_player_1"],
                "odds": row["odds_player_1"],
                "expected_value": row["ev_player_1"],
                "winner": row["actual_winner"] == row["player_1"]
            })
        if row["ev_player_2"] > args.ev_threshold and row["odds_player_2"] <= args.max_odds and row["odds_margin"] <= args.max_margin:
            bets.append({
                "player": row["player_2"],
                "predicted_prob": 1 - row["pred_prob_player_1"],
                "odds": row["odds_player_2"],
                "expected_value": row["ev_player_2"],
                "winner": row["actual_winner"] == row["player_2"]
            })

    bets_df = pd.DataFrame(bets)
    bets_df.to_csv(args.output_csv, index=False)

    print(f"✅ Saved {len(bets_df)} value bet candidates to {args.output_csv}")

    if len(bets_df) == 0:
        print("⚠️ No bets passed filtering — consider lowering --ev_threshold or raising --max_odds.")

    if args.debug:
        print(f"🔎 Total rows evaluated: {initial_rows}")
        print(f"EV threshold: {args.ev_threshold}")
        print(f"Odds cap: {args.max_odds}")
        print(f"Margin cap: {args.max_margin}")
        print(df[["player_1", "player_2", "odds_player_1", "odds_player_2", "pred_prob_player_1", "ev_player_1", "ev_player_2", "odds_margin"]].sort_values("ev_player_1", ascending=False).head(10))

if __name__ == "__main__":
    main()
