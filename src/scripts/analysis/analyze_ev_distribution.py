import argparse
import pandas as pd
import matplotlib.pyplot as plt
import glob
from pathlib import Path

from scripts.utils.normalize_columns import normalize_columns, patch_winner_column
from scripts.utils.betting_math import add_ev_and_kelly
from scripts.utils.logger import (
    log_info,
    log_success,
    log_warning,
    log_error,
    log_dryrun,
)
from scripts.utils.cli_utils import should_run, add_common_flags, assert_file_exists
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS


def main(args=None):
    """Analyze and plot EV distribution from value bet files."""
    parser = argparse.ArgumentParser(
        description="Analyze and plot EV distribution from value bet files."
    )
    parser.add_argument(
        "--value_bets_glob", required=True, help="Glob pattern for *_value_bets.csv"
    )
    parser.add_argument("--ev_threshold", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--max_odds", type=float, default=DEFAULT_MAX_ODDS)
    parser.add_argument("--output_csv", type=str, default=None)
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show the EV distribution plot interactively",
    )
    parser.add_argument(
        "--save_plot", action="store_true", help="Save the EV plot to disk"
    )
    add_common_flags(parser)
    _args = parser.parse_args(args)

    files = glob.glob(_args.value_bets_glob)
    if not files:
        raise ValueError(
            f"❌ No value bet files found matching: {_args.value_bets_glob}"
        )

    if _args.dry_run:
        log_dryrun(f"Would analyze files: {files}")
        return

    dfs = []
    for file in files:
        try:
            assert_file_exists(file, "value_bets_csv")
            df = pd.read_csv(file)
            df = normalize_columns(df)
            df = add_ev_and_kelly(df)
            df = patch_winner_column(df)
            df = df[
                (df["expected_value"] >= _args.ev_threshold)
                & (df["odds"] <= _args.max_odds)
            ]
            dfs.append(df)
        except Exception as e:
            log_warning(f"⚠️ Skipping {file}: {e}")

    if not dfs:
        raise ValueError("❌ No valid value bet files after filtering.")

    all_bets = pd.concat(dfs, ignore_index=True)
    log_info(f"📊 Loaded {len(all_bets)} filtered value bets")

    if _args.output_csv:
        output_path = Path(_args.output_csv)
        if should_run(output_path, _args.overwrite, _args.dry_run):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            all_bets.to_csv(output_path, index=False)
            log_success(f"✅ Saved filtered bets to {output_path}")

    if all_bets.empty:
        log_warning("⚠️ No data available for plotting.")
        return

    plt.figure(figsize=(10, 5))
    plt.hist(all_bets["expected_value"], bins=25, edgecolor="black")
    plt.title("EV Distribution (Filtered)")
    plt.xlabel("Expected Value")
    plt.ylabel("Number of Bets")
    plt.grid(True)

    if _args.save_plot:
        if not _args.output_csv:
            raise ValueError(
                "❌ --save_plot requires --output_csv to determine image path"
            )
        plot_path = Path(_args.output_csv).with_name(
            Path(_args.output_csv).stem + "_ev_distribution.png"
        )
        if should_run(plot_path, _args.overwrite, _args.dry_run):
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_path)
            log_success(f"🖼️ Saved EV distribution plot to {plot_path}")

    if _args.plot:
        plt.show()


if __name__ == "__main__":
    main()
