import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)

    # Core columns
    df["odds_player_1"] = pd.to_numeric(df["odds_player_1"], errors="coerce")
    df["odds_player_2"] = pd.to_numeric(df["odds_player_2"], errors="coerce")
    df["pred_prob_player_1"] = pd.to_numeric(df["pred_prob_player_1"], errors="coerce")

    # EV calculation
    df["ev_p1_model"] = df["pred_prob_player_1"] * df["odds_player_1"] - 1
    df["ev_p2_model"] = (1 - df["pred_prob_player_1"]) * df["odds_player_2"] - 1

    # ✅ Add for compatibility with bankroll sim
    df["p_model"] = df["pred_prob_player_1"]

    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved value bet candidates to {args.output_csv}")

if __name__ == "__main__":
    main()
