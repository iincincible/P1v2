import pandas as pd
import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def compute_roi(group, use_kelly=False):
    wins = group[group["actual_winner"] == group["player"]]
    total_staked = group["stake"].sum()
    total_return = wins["stake"] * (group["odds"] - 1) + wins["stake"]
    return (total_return.sum() - total_staked) / total_staked * 100 if total_staked > 0 else np.nan

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds_csv", required=True)
    parser.add_argument("--ev_bins", nargs="+", type=float, default=[0.1, 0.2, 0.3, 0.4, 0.5, 1.0])
    parser.add_argument("--max_odds", type=float, default=100.0)
    parser.add_argument("--save_plot", type=str, default=None)
    parser.add_argument("--save_csv", type=str, default=None)
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
        bet_df["stake_flat"] = 1
        bet_df["stake_kelly"] = (bet_df["predicted_prob"] * (bet_df["odds"] - 1) - (1 - bet_df["predicted_prob"])) / (bet_df["odds"] - 1)
        bet_df["stake_kelly"] = bet_df["stake_kelly"].clip(lower=0)
        bet_df = bet_df[["player", "predicted_prob", "odds", "expected_value", "actual_winner", "stake_flat", "stake_kelly"]]
        bets.append(bet_df)

    all_bets = pd.concat(bets)
    all_bets = all_bets[all_bets["odds"] <= args.max_odds]
    all_bets = all_bets[all_bets["expected_value"] >= min(args.ev_bins)]
    all_bets["ev_bin"] = pd.cut(all_bets["expected_value"], bins=args.ev_bins, right=False)

    def summarize(bin_group):
        return pd.Series({
            "Count": len(bin_group),
            "ROI (Flat %)": compute_roi(bin_group.assign(stake=bin_group["stake_flat"])),
            "ROI (Kelly %)": compute_roi(bin_group.assign(stake=bin_group["stake_kelly"]))
        })

    summary = all_bets.groupby("ev_bin").apply(summarize).reset_index()

    print("\n📊 ROI by Expected Value Bin:")
    print(summary)

    if args.save_csv:
        Path(args.save_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.save_csv, index=False)
        print(f"✅ Saved bin summary to {args.save_csv}")

    if args.save_plot:
        plt.figure(figsize=(9, 6))
        x = summary["ev_bin"].astype(str)
        plt.bar(x, summary["ROI (Flat %)"], label="Flat", alpha=0.7)
        plt.bar(x, summary["ROI (Kelly %)"], label="Kelly", alpha=0.7)
        plt.axhline(0, color="red", linestyle="--")
        plt.title("ROI by Expected Value Bin")
        plt.xlabel("Expected Value Bin")
        plt.ylabel("ROI (%)")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        Path(args.save_plot).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(args.save_plot)
        print(f"🖼️ Saved plot to {args.save_plot}")
        plt.close()

if __name__ == "__main__":
    main()
