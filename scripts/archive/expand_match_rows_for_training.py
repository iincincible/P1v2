import pandas as pd
import argparse

def expand_matches(input_csv, output_csv):
    print(f"🔍 Reading: {input_csv}")
    df = pd.read_csv(input_csv)

    # Drop rows missing key values
    df = df.dropna(subset=["player_1", "player_2", "winner_name", "odds_player_1", "odds_player_2"])

    rows = []
    for _, row in df.iterrows():
        # Row where player_1 is player_1
        rows.append({
            "player_1": row["player_1"],
            "player_2": row["player_2"],
            "winner_name": row["winner_name"],
            "odds_player_1": row["odds_player_1"],
            "odds_player_2": row["odds_player_2"],
            "odds_margin": row.get("odds_margin", None),
            "implied_prob_1": row.get("implied_prob_1", None),
            "implied_prob_2": row.get("implied_prob_2", None),
            "implied_diff": row.get("implied_diff", None),
            "won": int(row["player_1"] == row["winner_name"])
        })

        # Row where player_1 is flipped
        rows.append({
            "player_1": row["player_2"],
            "player_2": row["player_1"],
            "winner_name": row["winner_name"],
            "odds_player_1": row["odds_player_2"],
            "odds_player_2": row["odds_player_1"],
            "odds_margin": row.get("odds_margin", None),
            "implied_prob_1": row.get("implied_prob_2", None),
            "implied_prob_2": row.get("implied_prob_1", None),
            "implied_diff": -row.get("implied_diff", 0),
            "won": int(row["player_2"] == row["winner_name"])
        })

    out_df = pd.DataFrame(rows)
    print(f"✅ Expanded to {len(out_df)} training rows ({len(out_df) // 2} matches)")

    # Check balance
    print(out_df["won"].value_counts())

    out_df.to_csv(output_csv, index=False)
    print(f"✅ Saved expanded training set to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    expand_matches(args.input_csv, args.output_csv)
