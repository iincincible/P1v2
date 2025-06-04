import pandas as pd
from thefuzz import fuzz
from tqdm import tqdm
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    # Load Sackmann ATP match list
    matches = pd.read_csv(args.match_csv)
    matches["match_date"] = pd.to_datetime(matches["tourney_date"], errors="coerce")

    # Build set of player names
    player_names = set(matches["winner_name"].dropna().tolist() + matches["loser_name"].dropna().tolist())
    player_names = [p.lower() for p in player_names]

    # Load Betfair snapshots
    snaps = pd.read_csv(args.snapshots_csv)
    snaps["market_time"] = pd.to_datetime(snaps["market_time"], errors="coerce")
    snaps["runner_clean"] = snaps["runner_name"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
    snaps = snaps.dropna(subset=["runner_clean", "market_time"])

    print(f"🔍 Loaded {len(snaps)} snapshot rows")
    print(f"🔍 Matching against {len(player_names)} known players")

    # Fuzzy match runners to known player names
    matched_rows = []
    for _, snap_row in tqdm(snaps.iterrows(), total=len(snaps), desc="🧠 Filtering"):
        runner = snap_row["runner_clean"]

        # If any known player name matches the runner fuzzily
        if any(fuzz.partial_ratio(runner, p) >= 85 for p in player_names):
            matched_rows.append(snap_row)

    print(f"✅ Matched {len(matched_rows)} snapshot rows to known players")

    # Save output
    out_df = pd.DataFrame(matched_rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.output_csv, index=False)
    print(f"📁 Saved filtered snapshots to {args.output_csv}")

if __name__ == "__main__":
    main()
