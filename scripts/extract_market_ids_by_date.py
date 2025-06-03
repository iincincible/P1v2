import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Full metadata file, e.g. parsed/betfair_wta_markets_2023.csv")
    parser.add_argument("--target_date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--output_csv", required=True, help="Output file to save matched market_ids")
    args = parser.parse_args()

    # Load metadata
    df = pd.read_csv(args.input_csv, parse_dates=["market_time"])
    df["date"] = df["market_time"].dt.date

    # Filter by target date
    target = pd.to_datetime(args.target_date).date()
    filtered = df[df["date"] == target]

    # Drop duplicates and save
    out_df = filtered[["market_id"]].drop_duplicates()
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.output_csv, index=False)

    print(f"✅ Extracted {len(out_df)} market_ids for {target} from {args.input_csv}")
    print(f"📁 Saved to {args.output_csv}")

if __name__ == "__main__":
    main()
