import pandas as pd
import argparse
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds_csv", required=True)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.preds_csv)

    # Confirm expected columns
    required = ["odds_player_1", "odds_player_2", "pred_prob_player_1", "player_1", "player_2", "actual_winner"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Missing columns: {missing}")

    # Compute derived values
    df["pred_prob_player_2"] = 1 - df["pred_prob_player_1"]

    for i in [1, 2]:
        df[f"ev_player_{i}"] = df[f"pred_prob_player_{i}"] * (df[f"odds_player_{i}"] - 1) - (1 - df[f"pred_prob_player_{i}"])

    # Flatten to long format
    bets = []
    for i in [1, 2]:
        bets.append(df.assign(
            player=df[f"player_{i}"],
            predicted_prob=df[f"pred_prob_player_{i}"],
            odds=df[f"odds_player_{i}"],
            expected_value=df[f"ev_player_{i}"],
            won=(df["actual_winner"] == df[f"player_{i}"])
        )[["player", "predicted_prob", "odds", "expected_value", "won"]])

    all_bets = pd.concat(bets, ignore_index=True)

    # Filter bad rows
    all_bets = all_bets.dropna(subset=["expected_value", "odds"])

    # Bin by EV and odds
    ev_bins = pd.cut(all_bets["expected_value"], bins=[-1, 0, 0.02, 0.05, 0.1, 0.2, 1])
    odds_bins = pd.cut(all_bets["odds"], bins=[0, 1.5, 2.0, 3.0, 5.0, 10.0, 100])

    ev_summary = all_bets.groupby(ev_bins)["expected_value"].agg(["count", "mean"])
    odds_summary = all_bets.groupby(odds_bins)["expected_value"].agg(["count", "mean"])

    print("\n📊 Expected Value Distribution (EV bins):")
    print(ev_summary)

    print("\n📊 Expected Value by Odds Range:")
    print(odds_summary)

    if args.plot:
        import seaborn as sns
        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 5))
        sns.histplot(all_bets["expected_value"], bins=30, kde=True)
        plt.title("Distribution of Expected Value")
        plt.xlabel("Expected Value")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
