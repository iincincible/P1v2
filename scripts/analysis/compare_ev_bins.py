import pandas as pd
import argparse
import matplotlib.pyplot as plt
import numpy as np

def compute_roi(group):
    wins = group[group["actual_winner"] == group["player"]]
    total_staked = len(group)
    total_return = wins["odds"].sum()
    return (total_return - total_staked) / total_staked * 100 if total_staked > 0 else np.nan

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds_csv", required=True)
    parser.add_argument("--ev_bins", nargs="+", type=float, default=[0.1, 0.2, 0.3, 0.4, 0.5, 1.0])
    parser.add_argument("--max_odds", type=float, default=100.0)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.preds_csv)

    required_cols = ["player_1", "player_2", "odds_player_1", "odds_player_2",
                     "pred_prob_player_1", "actual_winner"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing required columns: {missing}")

    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]
    df["ev_player_1"] = df["pred_prob_player_1"] * (df["odds_player_1"] - 1) - (1 - df["pred_prob_player_1"])
    df["ev_player_2"] = df["pred_prob_player_2"] * (df["odds_player_2"] - 1) - (1 - df["pred_prob_player_2"])

    bets = []
    for i in [1, 2]:
        bet_df = df.copy()
        bet_df["player"] = bet_df[f"player_{i}"]
        bet_df["predicted_prob"] = bet_df[f"pred_prob_player_{i}"]
        bet_df["odds"] = bet_df[f"odds_player_{i}"]
        bet_df["expected_value"] = bet_df[f"ev_player_{i}"]
        bets.append(bet_df[["player", "predicted_prob", "odds", "expected_value", "actual_winner"]])

    all_bets = pd.concat(bets)
    all_bets = all_bets[all_bets["odds"] <= args.max_odds]
    all_bets = all_bets[all_bets["expected_value"] >= min(args.ev_bins)]

    all_bets["ev_bin"] = pd.cut(all_bets["expected_value"], bins=args.ev_bins, right=False)
    summary = all_bets.groupby("ev_bin").apply(compute_roi).reset_index(name="ROI (%)")

    print("\n📊 ROI by Expected Value Bin:")
    print(summary)

    if args.plot:
        plt.figure(figsize=(8, 5))
        plt.bar(summary["ev_bin"].astype(str), summary["ROI (%)"], color="lightgreen", edgecolor="black")
        plt.axhline(y=0, color="red", linestyle="--")
        plt.title("ROI by Expected Value Bin")
        plt.ylabel("ROI (%)")
        plt.xlabel("Expected Value Bin")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
