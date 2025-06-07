import argparse
import pandas as pd
from pathlib import Path

def extract_by_snapshot(input_csv, output_csv):
    df = pd.read_csv(input_csv, usecols=["market_id"])
    df["market_id"] = df["market_id"].astype(str)
    df["market_id"].dropna().drop_duplicates().to_frame().to_csv(output_csv, index=False)
    print(f"✅ Extracted {df['market_id'].nunique()} market_ids from snapshot to {output_csv}")

def extract_by_metadata(input_csv, target_date, output_csv):
    df = pd.read_csv(input_csv, parse_dates=["market_time"])
    df["date"] = df["market_time"].dt.date
    filtered = df[df["date"] == pd.to_datetime(target_date).date()]
    filtered[["market_id"]].drop_duplicates().to_csv(output_csv, index=False)
    print(f"✅ Found {len(filtered)} market_ids for {target_date}, saved to {output_csv}")

def extract_by_range(input_csv, dates, output_csv):
    df = pd.read_csv(input_csv, parse_dates=["market_time"])
    df["date"] = df["market_time"].dt.date.astype(str)
    filtered = df[df["date"].isin(dates)]
    filtered[["market_id"]].drop_duplicates().to_csv(output_csv, index=False)
    print(f"✅ Merged {len(filtered)} market_ids across dates {dates}, saved to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["snapshot", "metadata", "range"], required=True)
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--target_date", help="YYYY-MM-DD (for metadata mode)")
    parser.add_argument("--date_list", help="Comma-separated YYYY-MM-DD dates (for range mode)")
    args = parser.parse_args()

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "snapshot":
        extract_by_snapshot(args.input_csv, args.output_csv)
    elif args.mode == "metadata":
        if not args.target_date:
            raise ValueError("Missing --target_date for metadata mode")
        extract_by_metadata(args.input_csv, args.target_date, args.output_csv)
    elif args.mode == "range":
        if not args.date_list:
            raise ValueError("Missing --date_list for range mode")
        dates = [d.strip() for d in args.date_list.split(",")]
        extract_by_range(args.input_csv, dates, args.output_csv)

if __name__ == "__main__":
    main()
