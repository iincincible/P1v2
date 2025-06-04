import argparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from pathlib import Path

# Tournament-specific fallback dates
TOURNAMENT_DATES = {
    "aus_open": "2023-01-20",
    "french_open": "2023-06-01",
    "wimbledon": "2023-07-07",
    "us_open": "2023-09-01",
}

def infer_tournament_date(file_path: str) -> str:
    for key, date in TOURNAMENT_DATES.items():
        if key in file_path.lower():
            return pd.to_datetime(date)
    return pd.to_datetime("2023-01-01")  # default fallback

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csvs", nargs='+', required=True, help="List of bankroll CSV files to combine")
    parser.add_argument("--output_csv", required=True, help="Path to save combined bankroll CSV")
    parser.add_argument("--plot_path", required=True, help="Path to save bankroll plot image")
    args = parser.parse_args()

    combined = []
    for csv_file in args.input_csvs:
        df = pd.read_csv(csv_file)
        df["source_file"] = Path(csv_file).name
        df["date"] = infer_tournament_date(csv_file)
        combined.append(df)

    if not combined:
        raise FileNotFoundError(f"No files matched: {args.input_csvs}")

    df_all = pd.concat(combined).sort_values("date").reset_index(drop=True)
    df_all["cumulative_bankroll"] = df_all["bankroll"]

    # Keep max bankroll across files
    df_all["cumulative_bankroll"] = df_all.groupby("date")["bankroll"].transform("last").cumsum()

    print("\n📆 Preview of assigned tournament dates:")
    print(df_all[["source_file", "date"]].drop_duplicates().sort_values("date"))

    final_bankroll = df_all["cumulative_bankroll"].iloc[-1]
    initial_bankroll = 1000.0
    roi = 100 * (final_bankroll - initial_bankroll) / initial_bankroll
    drawdowns = df_all["cumulative_bankroll"].cummax() - df_all["cumulative_bankroll"]
    max_drawdown = drawdowns.max()

    # Save combined CSV
    df_all.to_csv(args.output_csv, index=False)

    # Plot bankroll
    plt.figure(figsize=(12, 6))
    plt.plot(df_all["date"], df_all["cumulative_bankroll"], marker='o', linestyle='-')
    plt.title("Cumulative Bankroll Across Tournaments (2023)")
    plt.xlabel("Tournament Date")
    plt.ylabel("Cumulative Bankroll")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.plot_path)

    print(f"\n📈 Simulated {len(df_all)} bets")
    print(f"💰 Final bankroll: {final_bankroll:,.2f}")
    print(f"💹 ROI: {roi:.2f}%")
    print(f"📉 Max drawdown: {max_drawdown:,.2f}")
    print(f"📈 Plot saved to {args.plot_path}")

if __name__ == "__main__":
    main()
