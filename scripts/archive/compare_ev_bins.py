import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

def analyze_ev_bins(df, ev_column, outcome_column, odds_column, bin_size, min_bets_per_bin):
    df = df.copy()
    df['ev_bin'] = (df[ev_column] / bin_size).astype(int) * bin_size

    bin_stats = []
    for ev_bin, group in df.groupby('ev_bin'):
        if len(group) < min_bets_per_bin:
            continue
        n = len(group)
        roi = ((group[outcome_column] * (group[odds_column] - 1)).sum() - (n - group[outcome_column].sum())) / n
        avg_ev = group[ev_column].mean()
        bin_stats.append({'ev_bin': ev_bin, 'roi': roi, 'n_bets': n, 'avg_ev': avg_ev})

    return pd.DataFrame(bin_stats).sort_values('ev_bin')

def main():
    parser = argparse.ArgumentParser(description="Compare ROI by expected value (EV) bins.")
    parser.add_argument('--preds_csv', type=str, required=True, help='CSV with predictions and outcomes')
    parser.add_argument('--ev_column', type=str, required=True, help='Name of expected value column (e.g., expected_value)')
    parser.add_argument('--outcome_column', type=str, default='won', help='Column name indicating if the bet won (default: won)')
    parser.add_argument('--odds_column', type=str, default='odds', help='Column with odds used for ROI calculation')
    parser.add_argument('--bin_size', type=float, default=0.05, help='Bin size for EV buckets')
    parser.add_argument('--min_bets_per_bin', type=int, default=5, help='Minimum number of bets required to include bin')
    parser.add_argument('--save_csv', type=str, help='Path to save the bin ROI analysis CSV')
    parser.add_argument('--save_plot', type=str, help='Path to save the ROI plot image')

    args = parser.parse_args()

    df = pd.read_csv(args.preds_csv)
    required_cols = [args.ev_column, args.outcome_column, args.odds_column]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column: {col}")

    print(f"✅ Loaded {len(df)} rows")

    results = analyze_ev_bins(df, args.ev_column, args.outcome_column, args.odds_column, args.bin_size, args.min_bets_per_bin)
    print(results)

    if args.save_csv:
        results.to_csv(args.save_csv, index=False)
        print(f"✅ Saved analysis to {args.save_csv}")

    if args.save_plot:
        sns.set(style='whitegrid')
        plt.figure(figsize=(10, 6))
        sns.barplot(data=results, x='ev_bin', y='roi', color='dodgerblue')
        plt.axhline(0, linestyle='--', color='gray')
        plt.title('ROI by EV Bin')
        plt.xlabel('Expected Value Bin')
        plt.ylabel('ROI')
        plt.tight_layout()
        plt.savefig(args.save_plot)
        print(f"🖼️ Saved plot to {args.save_plot}")

if __name__ == "__main__":
    main()
