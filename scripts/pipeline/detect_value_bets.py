import argparse
import pandas as pd

def detect_value_bets(input_csv, output_csv, max_odds=10.0, max_margin=0.10, ev_threshold=0.0):
    df = pd.read_csv(input_csv, low_memory=False)

    # Derive missing columns
    df["pred_prob_1"] = df["pred_prob_player_1"]
    df["pred_prob_2"] = 1 - df["pred_prob_1"]

    # Compute expected value for each player
    for i in [1, 2]:
        prob_col = f"pred_prob_{i}"
        odds_col = f"odds_player_{i}"
        df[f"ev_player_{i}"] = df[prob_col] * (df[odds_col] - 1) - (1 - df[prob_col])

    # Filter bets by margin, odds, and EV threshold
    df = df[df["odds_margin"] <= max_margin]
    df = df[(df["odds_player_1"] <= max_odds) & (df["odds_player_2"] <= max_odds)]

    # Stack into long format
    rows = []
    for i in [1, 2]:
        rows.append(df.assign(
            player=df[f"player_{i}"],
            predicted_prob=df[f"pred_prob_{i}"],
            odds=df[f"odds_player_{i}"],
            expected_value=df[f"ev_player_{i}"],
            winner=(df["actual_winner"] == df[f"player_{i}"]),
        )[["player", "predicted_prob", "odds", "expected_value", "winner"]])

    bets = pd.concat(rows, ignore_index=True)
    bets = bets[bets["expected_value"] > ev_threshold]
    bets = bets.sort_values("expected_value", ascending=False)

    bets.to_csv(output_csv, index=False)
    print(f"✅ Saved value bet candidates to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--max_odds", type=float, default=10.0)
    parser.add_argument("--max_margin", type=float, default=0.10)
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    args = parser.parse_args()

    detect_value_bets(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        max_odds=args.max_odds,
        max_margin=args.max_margin,
        ev_threshold=args.ev_threshold
    )

if __name__ == "__main__":
    main()
