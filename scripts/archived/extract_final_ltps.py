import pandas as pd
import argparse

def extract_final_ltps(input_csv, output_csv):
    df = pd.read_csv(input_csv, parse_dates=["timestamp"])
    df = df.dropna(subset=["ltp", "market_id", "selection_id"])

    df_sorted = df.sort_values("timestamp")
    final_ltps = df_sorted.groupby(["market_id", "selection_id"]).last().reset_index()

    final_ltps = final_ltps[["market_id", "selection_id", "ltp"]]
    final_ltps.to_csv(output_csv, index=False)
    print(f"✅ Extracted {len(final_ltps)} final LTPs to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    extract_final_ltps(args.input_csv, args.output_csv)
