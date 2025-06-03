import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--cap", type=float, default=10.0)
    args = parser.parse_args()

    print(f"✨ Loading {args.input_csv}")
    df = pd.read_csv(args.input_csv, low_memory=False)
    print(f"✨ Loaded {len(df)} rows")

    # Find odds columns, allowing for suffixes (_x, _y)
    print(f"🔍 Columns in input: {df.columns.tolist()}")
    odds_1_cols = [c for c in df.columns if c.startswith("odds_player_1")]
    odds_2_cols = [c for c in df.columns if c.startswith("odds_player_2")]

    if not odds_1_cols:
        raise ValueError("❌ Missing column: odds_player_1 (any suffix)")
    if not odds_2_cols:
        raise ValueError("❌ Missing column: odds_player_2 (any suffix)")

    if len(odds_1_cols) > 1:
        print(f"⚠️ Multiple candidates for odds_player_1: {odds_1_cols}, using first")
    if len(odds_2_cols) > 1:
        print(f"⚠️ Multiple candidates for odds_player_2: {odds_2_cols}, using first")

    df["odds_player_1"] = pd.to_numeric(df[odds_1_cols[0]], errors="coerce")
    df["odds_player_2"] = pd.to_numeric(df[odds_2_cols[0]], errors="coerce")

    # Drop rows with missing odds
    df = df.dropna(subset=["odds_player_1", "odds_player_2"])
    print(f"🧹 Dropped to {len(df)} rows with valid odds")

    # Cap high odds
    df["odds_player_1"] = df["odds_player_1"].clip(upper=args.cap)
    df["odds_player_2"] = df["odds_player_2"].clip(upper=args.cap)
    print(f"🔐 Capped odds at {args.cap}")

    # Compute implied probabilities
    df["implied_prob_1"] = 1 / df["odds_player_1"]
    df["implied_prob_2"] = 1 / df["odds_player_2"]

    # Compute margin and implied prob diff
    df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
    df["implied_diff"] = df["implied_prob_1"] - df["implied_prob_2"]

    # Save output
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} rows with odds features to {args.output_csv}")

if __name__ == "__main__":
    main()
