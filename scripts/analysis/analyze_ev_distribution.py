import argparse
import pandas as pd
import matplotlib.pyplot as plt
import glob
from pathlib import Path

from scripts.utils.normalize_columns import normalize_columns
from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import should_run, add_common_flags


def main():
    parser = argparse.ArgumentParser(description="Analyze and plot EV distribution from value bet files.")
    parser.add_argument("--value_bets_glob", required=True, help="Glob pattern for *_value_bets.csv")
    parser.add_argument("--ev_threshold", type=float, default=0.2)
    parser.add_argument("--max_odds", type=float, default=6.0)
    parser.add_argument("--output_csv", type=str, default=None)
    parser.add_argument("--plot", action="store_true", help="Show the EV distribution plot interactively")
    parser.add_argument("--save_plot", action="store_true", help="Save the EV plot to disk")
    add_common_flags(parser)
    args = parser.parse_args()

    files = glob.glob(args.value_bets_glob)
    if not files:
        raise ValueError("No value bet files found.")

    if args.output_csv:
        output_path = Path(args.output_csv)
        if not should_run(output_path, args.overwrite, args.dry_run):
            return

    if args.save_plot and args.output_csv:
        plot_path = Path(args.output_csv).with_name(Path(args.output_csv).stem + "_ev_distribution.png")
        if not should_run(plot_path, args.overwrite, args.dry_run):
            return

    dfs = []
    for file in files:
        df = pd.read_csv(file)
        df = normalize_columns(df)
        df = df[df["expected_value"] >= args.ev_threshold]
        df = df[df["odds"] <= args.max_odds]
        dfs.append(df)

    all_bets = pd.concat(dfs, ignore_index=True)
    log_info(f"📊 Loaded {len(all_bets)} value bets after filtering")

    if args.output_csv:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        all_bets.to_csv(output_path, index=False)
        log_success(f"✅ Saved filtered bets to {output_path}")

    # === Plot EV histogram ===
    plt.figure(figsize=(10, 5))
    plt.hist(all_bets["expected_value"], bins=25, color="blue", edgecolor="black")
    plt.title("EV Distribution (Filtered)")
    plt.xlabel("Expected Value")
    plt.ylabel("Number of Bets")
    plt.grid(True)

    if args.save_plot:
        out_path = (
            Path(args.output_csv).with_name(Path(args.output_csv).stem + "_ev_distribution.png")
            if args.output_csv else Path("ev_distribution.png")
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path)
        log_success(f"🖼️ Saved EV distribution plot to {out_path}")

    if args.plot:
        plt.show()


if __name__ == "__main__":
    main()
