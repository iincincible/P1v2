import pandas as pd
import argparse
from tqdm import tqdm

def expand_rows(input_csv, output_csv):
    df = pd.read_csv(input_csv, low_memory=False)
    rows = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="🔁 Expanding"):
        # Row for player_1
        row1 = row.copy()
        row1["player"] = row["player_1"]
        row1["opp"] = row["player_2"]
        row1["odds"] = row["odds_player_1"]
        row1["won"] = int(row["player_1"] == row["winner_name"])
        rows.append(row1)

        # Row for player_2
        row2 = row.copy()
        row2["player"] = row["player_2"]
        row2["opp"] = row["player_1"]
        row2["odds"] = row["odds_player_2"]
        row2["won"] = int(row["player_2"] == row["winner_name"])
        rows.append(row2)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_csv, index=False)
    print(f"✅ Expanded to {len(out_df)} rows")
    print(f"✅ Saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    expand_rows(args.input_csv, args.output_csv)
