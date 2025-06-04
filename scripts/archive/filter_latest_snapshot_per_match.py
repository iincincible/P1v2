import pandas as pd
import argparse

def deduplicate(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # Check and preserve odds columns
    odds_cols = ["odds_player_1", "odds_player_2"]
    if not all(col in df.columns for col in odds_cols):
        print("⚠️ Odds columns missing before deduplication.")
    else:
        print("✅ Odds columns detected and will be preserved.")

    df_sorted = df.sort_values("snapshot_date" if "snapshot_date" in df.columns else df.columns[0])
    deduped = df_sorted.drop_duplicates(subset=["player_1", "player_2"], keep="last")

    deduped.to_csv(output_csv, index=False)
    print(f"✅ Deduplicated: {len(df)} → {len(deduped)} rows saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()
    deduplicate(args.input_csv, args.output_csv)
