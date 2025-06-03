import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Path to snapshot CSV")
    parser.add_argument("--output_csv", required=True, help="Path to save unique market_ids")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv, low_memory=False)
    market_ids = df["market_id"].dropna().astype(str).unique()
    pd.DataFrame({"market_id": market_ids}).to_csv(args.output_csv, index=False)
    print(f"✅ Extracted {len(market_ids)} market_ids from {args.input_csv}")
    print(f"📁 Saved to {args.output_csv}")

if __name__ == "__main__":
    main()
