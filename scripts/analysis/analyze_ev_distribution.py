import pandas as pd
import argparse
import matplotlib.pyplot as plt

def compute_ev(prob, odds):
    return prob * (odds - 1) - (1 - prob)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.0)
    parser.add_argument("--max_odds", type=float, default=100.0)
    parser.add_argument("--output_csv", type=str, help="Optional: path to save filtered EV rows")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.preds_csv)

    required_cols = ["odds_player_1", "odds_player_2", "pred_prob_player_1", "player_1", "player_2", "actual_winner"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing required columns: {missing}")

    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]
    df["ev_player_1"] = compute_ev(df["pred_prob_player_1"], df["odds_player_1"])
    df["ev_player_2"] = compute_ev(df["pred_prob_player_2"], df["odds_player_2"])

    bets = []
    for i in [1, 2]:
        bet_df = df.copy()
        bet_df["player"] = bet_df[f"player_{i}"]
        bet_df["predicted_prob"] = bet_df[f"pred_prob_player_{i}"]
        bet_df["odds"] = bet_df[f"odds_player_{i}"]
        bet_df["expected_value"] = bet_df[f"ev_player_{i}"]
        bets.append(bet_df[["player", "predicted_prob", "odds", "expected_value"]])

    all_bets = pd.concat(bets)
    filtered = all_bets[
        (all_bets["expected_value"] > args.ev_threshold) &
        (all_bets["odds"] <= args.max_odds)
    ]

    print(f"✅ Total bets: {len(all_bets)}")
    print(f"📈 Value bets (EV > {args.ev_threshold}, odds ≤ {args.max_odds}): {len(filtered)}")

    if args.output_csv:
        filtered.to_csv(args.output_csv, index=False)
        print(f"💾 Saved filtered EV bets to {args.output_csv}")

    if args.plot:
        plt.hist(filtered["expected_value"], bins=30, color="skyblue", edgecolor="black")
        plt.axvline(x=0, color="red", linestyle="--")
        plt.title("Distribution of Expected Value")
        plt.xlabel("Expected Value")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
