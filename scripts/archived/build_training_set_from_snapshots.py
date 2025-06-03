import pandas as pd
import argparse

def build_training_set(input_csv, output_csv):
    print(f"🔍 Reading: {input_csv}")
    df = pd.read_csv(input_csv)

    # Step 1: Remove rows missing odds or players
    df = df.dropna(subset=["odds_player_1", "odds_player_2", "player_1", "player_2", "winner_name"])

    # Step 2: Drop duplicate matches (one row per unique matchup+market)
    df = df.drop_duplicates(subset=["player_1", "player_2", "market_id"])

    # Step 3: Rebuild the label
    df["won"] = (df["player_1"] == df["winner_name"]).astype(int)

    # Step 4: Confirm class balance
    label_counts = df["won"].value_counts()
    print(f"✅ Class counts:\n{label_counts}")

    # Step 5: Output result
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved cleaned training set to {output_csv} ({len(df)} rows)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    build_training_set(args.input_csv, args.output_csv)
