import pandas as pd
import argparse

def cap_odds(df: pd.DataFrame, cap: float) -> pd.DataFrame:
    for col in ['odds_player_1', 'odds_player_2']:
        if col not in df.columns:
            raise ValueError(f"Missing expected column: {col}")
        df[col] = df[col].clip(upper=cap)
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--cap", type=float, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    df = cap_odds(df, cap=args.cap)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Capped odds and saved to {args.output_csv}")

if __name__ == "__main__":
    main()
