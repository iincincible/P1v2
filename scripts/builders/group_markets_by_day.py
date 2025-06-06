import pandas as pd
import argparse
from pathlib import Path
from scripts.utils.logger import log_info, log_success

def normalize_name(x):
    return str(x).strip().upper()

def group_by_day(input_csv: str, output_csv: str):
    log_info(f"Loading: {input_csv}")
    df = pd.read_csv(input_csv, parse_dates=["market_time"])

    if not {"runner_1", "runner_2"}.issubset(df.columns):
        raise ValueError("❌ Input must contain 'runner_1' and 'runner_2' columns.")

    df["date"] = df["market_time"].dt.date
    df["runner_1_clean"] = df["runner_1"].map(normalize_name)
    df["runner_2_clean"] = df["runner_2"].map(normalize_name)

    grouped = (
        df.groupby("date")
        .agg(
            num_markets=("market_id", "nunique"),
            unique_runners=("runner_1_clean", lambda x: len(set(x)) + len(set(df.loc[x.index, "runner_2_clean"])))
        )
        .reset_index()
        .sort_values("date")
    )

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(output_csv, index=False)
    log_success(f"Saved grouped summary to {output_csv}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Parsed metadata with market_time, runner_1/2")
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    group_by_day(args.input_csv, args.output_csv)

if __name__ == "__main__":
    main()
