import pandas as pd
import argparse

def filter_ausopen(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    ausopen = df[df["tourney_name"] == "Australian Open"]
    ausopen.to_csv(output_csv, index=False)
    print(f"✅ Filtered to {len(ausopen)} AUS Open matches → saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    filter_ausopen(args.input_csv, args.output_csv)
