import pandas as pd
import argparse

def patch_odds_margin_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    
    # Handle odds_player_1/2 missing or zero
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]

    # Clean up any invalid odds (0, inf)
    df.loc[~df["implied_prob_1"].between(0, 1), "implied_prob_1"] = None
    df.loc[~df["implied_prob_2"].between(0, 1), "implied_prob_2"] = None

    # Compute margin and prob diff
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    print(f"✅ Added odds_margin and implied_prob_diff to {len(df)} rows.")
    df.to_csv(output_csv, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    patch_odds_margin_features(args.input_csv, args.output_csv)
