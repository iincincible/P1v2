import pandas as pd
import argparse
from pathlib import Path
from scripts.utils.logger import log_info, log_success, log_warning

def extract_sackmann_matches(input_csv, tourney_substring, output_csv, start_date=None, end_date=None):
    log_info(f"Loading input: {input_csv}")
    df = pd.read_csv(input_csv, low_memory=False)

    # Convert date
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d", errors="coerce")

    # Filter by tournament name
    log_info(f"Filtering tournament name with: '{tourney_substring}'")
    df = df[df["tourney_name"].str.contains(tourney_substring, case=False, na=False)]

    # Optional date filtering
    if start_date:
        df = df[df["tourney_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["tourney_date"] <= pd.to_datetime(end_date)]

    if df.empty:
        log_warning("No matches found after filtering.")
    else:
        df["match_date"] = df["tourney_date"].dt.date
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        log_success(f"Saved {len(df)} matches to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Path to Sackmann match CSV")
    parser.add_argument("--tourney_substring", required=True, help="e.g. 'Indian Wells'")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--start_date", help="e.g. 2023-03-01", required=False)
    parser.add_argument("--end_date", help="e.g. 2023-03-15", required=False)
    args = parser.parse_args()

    extract_sackmann_matches(
        input_csv=args.input_csv,
        tourney_substring=args.tourney_substring,
        output_csv=args.output_csv,
        start_date=args.start_date,
        end_date=args.end_date
    )

if __name__ == "__main__":
    main()
