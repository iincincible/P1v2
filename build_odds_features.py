import argparse
import pandas as pd

def build_odds_features(df: pd.DataFrame, cap: float = None) -> pd.DataFrame:
    # Optional odds capping
    if cap is not None:
        for col in ["odds_player_1", "odds_player_2"]:
            if col in df.columns:
                df[col] = df[col].clip(upper=cap)

    # Implied probabilities
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]

    # Clean up invalid implied probabilities
    df.loc[~df["implied_prob_1"].between(0, 1), "implied_prob_1"] = None
    df.loc[~df["implied_prob_2"].between(0, 1), "implied_prob_2"] = None

    # Odds margin and difference
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"] - 1
    df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Input CSV with odds_player_1 and odds_player_2")
    parser.add_argument("--output_csv", required=True, help="Output CSV with added features")
    parser.add_argument("--cap", type=float, default=None, help="Optional cap for odds (e.g. 10.0)")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    df = build_odds_features(df, cap=args.cap)
    df.to_csv(args.output_csv, index=False)

    print(f"✅ Built odds features for {len(df)} rows → saved to {args.output_csv}")

if __name__ == "__main__":
    main()
