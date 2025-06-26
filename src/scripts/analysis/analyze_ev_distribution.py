import glob
import pandas as pd
import matplotlib.pyplot as plt

from scripts.utils.normalize_columns import (
    normalize_and_patch_canonical_columns,
    enforce_canonical_columns,
)
from scripts.utils.cli import guarded_run
from scripts.utils.logger import log_info, log_success, log_warning, setup_logging
from scripts.utils.constants import DEFAULT_EV_THRESHOLD, DEFAULT_MAX_ODDS
from scripts.utils.betting_math import add_ev_and_kelly


@guarded_run
def main(
    value_bets_glob: str,
    output_csv: str = None,
    ev_threshold: float = DEFAULT_EV_THRESHOLD,
    max_odds: float = DEFAULT_MAX_ODDS,
    plot: bool = False,
    save_plot: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Analyze and plot the EV distribution from value bet CSV files.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = glob.glob(value_bets_glob)
    if not files:
        raise ValueError(f"No value bet files found matching: {value_bets_glob}")

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df = normalize_and_patch_canonical_columns(df, context=f)
            df = add_ev_and_kelly(df)
            # Filtering
            df = df[(df["expected_value"] >= ev_threshold) & (df["odds"] <= max_odds)]
            dfs.append(df)
            log_info(f"Loaded {len(df)} bets from {f}")
        except Exception as e:
            log_warning(f"Skipping {f}: {e}")

    if not dfs:
        raise ValueError("No valid value bet files after filtering.")

    all_bets = pd.concat(dfs, ignore_index=True)
    enforce_canonical_columns(all_bets, context="analyze_ev_distribution")

    log_info(f"Loaded {len(all_bets)} filtered value bets across {len(files)} files.")

    print("\n========== EV Distribution Analysis ==========")
    print(f"Files analyzed: {files}")
    print("Number of value bets:", len(all_bets))
    print("\nEV (expected value) stats:")
    print(all_bets["expected_value"].describe())
    print("\nOdds stats:")
    print(all_bets["odds"].describe())
    print("\nTop 5 bets by EV:")
    print(
        all_bets.sort_values("expected_value", ascending=False)[
            ["player_1", "player_2", "odds", "expected_value", "winner"]
        ].head()
    )
    if "winner" in all_bets.columns:
        print("\nWin rate:", (all_bets["winner"] == 1).mean())
    print("=============================================\n")

    if output_csv:
        all_bets.to_csv(output_csv, index=False)
        log_success(f"Saved filtered bets to {output_csv}")

    if all_bets.empty:
        log_warning("No data available for plotting.")
        return

    plt.figure(figsize=(10, 5))
    plt.hist(all_bets["expected_value"], bins=25, edgecolor="black")
    plt.title("EV Distribution (Filtered)")
    plt.xlabel("Expected Value")
    plt.ylabel("Number of Bets")
    plt.grid(True)

    if save_plot:
        if not output_csv:
            raise ValueError(
                "--save_plot requires --output_csv to determine image path"
            )
        from pathlib import Path

        plot_path = Path(output_csv).with_name(
            Path(output_csv).stem + "_ev_distribution.png"
        )
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path)
        log_success(f"Saved EV distribution plot to {plot_path}")

    if plot:
        plt.show()


if __name__ == "__main__":
    main()
