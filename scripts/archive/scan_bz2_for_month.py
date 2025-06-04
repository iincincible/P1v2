import argparse
import os
import pandas as pd
from tqdm import tqdm

def scan_bz2_for_month(month_dir):
    records = []

    for root, _, files in os.walk(month_dir):
        for file in files:
            if file.endswith(".bz2"):
                full_path = os.path.join(root, file)
                market_id = os.path.basename(os.path.dirname(full_path))
                records.append({
                    "market_id": market_id,
                    "filepath": full_path  # <- critical field for downstream
                })

    return pd.DataFrame(records)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--month_dir", required=True, help="Top-level month folder (e.g., data/BASIC/2023/Jan)")
    parser.add_argument("--output_csv", required=True, help="Path to save the snapshot candidate CSV")
    args = parser.parse_args()

    print(f"🔍 Scanning BZ2 files under {args.month_dir} ...")
    df = scan_bz2_for_month(args.month_dir)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} snapshot candidates to {args.output_csv}")
