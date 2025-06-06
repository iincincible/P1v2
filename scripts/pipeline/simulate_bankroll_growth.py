import argparse
import pandas as pd
import os
import sys

# Patch import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.simulation import simulate_bankroll, generate_bankroll_plot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csvs", required=True, help="Comma-separated list of CSV files")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--ev_threshold", type=float, default=0.01)
    parser.add_argument("--odds_cap", type=float, default=10.0)
    parser.add_argument("--strategy", choices=["flat", "kelly"], default="flat")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    if os.path.exists(args.output_csv):
        print(f"⏭️ Output already exists: {args.output_csv}")
        return

    files = args.input_csvs.split(",")
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df = normalize_columns(df)

            if "winner" not in df.columns:
                if "actual_winner" in df.columns and "player_1" in df.columns:
                    df["winner"] = (
                        df["actual_winner"].str.strip().str.lower() ==
                        df["player_1"].str.strip().str.lower()
                    ).astype(int)
                    print(f"🩹 Patched 'winner' from actual_winner in: {f}")
                else:
                    raise ValueError("Cannot compute 'winner' — missing actual_winner or player_1")

            dfs.append(df)
        except Exception as e:
            print(f"⚠️ Skipping {f}: {e}")

    if not dfs:
        raise ValueError("❌ No valid input files after normalization and patching.")

    df = pd.concat(dfs, ignore_index=True)

    sim_df, final_bankroll, max_drawdown = simulate_bankroll(
        df,
        strategy=args.strategy,
        ev_threshold=args.ev_threshold,
        odds_cap=args.odds_cap,
        initial_bankroll=1000.0,
        cap_fraction=0.05
    )

    sim_df.to_csv(args.output_csv, index=False)
    print(f"\n📈 Simulated {len(sim_df)} bets")
    print(f"💰 Final bankroll: {final_bankroll:.2f}")
    print(f"📉 Max drawdown: {max_drawdown:.2f}")

    png_path = os.path.splitext(args.output_csv)[0] + ".png"
    generate_bankroll_plot(sim_df["bankroll"], output_path=png_path)

    if args.plot:
        import matplotlib.pyplot as plt
        plt.show()

if __name__ == "__main__":
    main()
