"""
Simulate bankroll growth over a series of value bets, using Kelly staking.
"""

import pandas as pd
from pathlib import Path

from scripts.utils.cli import guarded_run
from scripts.utils.logger import getLogger
from scripts.utils.value_metrics import compute_value_metrics
from scripts.utils.schema import SchemaManager

logger = getLogger(__name__)


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    initial_bankroll: float = 1000.0,
    dry_run: bool = False,
    overwrite: bool = False,
):
    """
    Perform a Kelly-based bankroll simulation given a list of value bets.

    Args:
        input_csv: CSV of value bets with 'odds', 'probability', and 'result' columns.
        output_csv: Path to write the simulation results CSV.
        initial_bankroll: Starting bankroll amount.
        dry_run: If True, process but do not write output.
        overwrite: If True, overwrite existing output file.
    """
    in_path = Path(input_csv)
    if not in_path.exists():
        logger.error("Input CSV not found: %s", in_path)
        raise FileNotFoundError(in_path)

    df = pd.read_csv(in_path)
    logger.info("Loaded %d bets from %s", len(df), in_path)

    # Compute EV and Kelly metrics
    df_metrics = compute_value_metrics(df)

    # Initialize bankroll column
    df_metrics.insert(0, "bankroll", initial_bankroll)

    # Simulate sequentially
    for idx in df_metrics.index[1:]:
        prev_bank = df_metrics.at[idx - 1, "bankroll"]
        kelly = df_metrics.at[idx - 1, "kelly_fraction"]
        bet_amount = prev_bank * kelly
        outcome = df_metrics.at[idx - 1, "result"]  # 1 for win, 0 for loss
        odds = df_metrics.at[idx - 1, "odds"]
        # Update bankroll
        pnl = bet_amount * (odds - 1) * outcome - bet_amount * (1 - outcome)
        df_metrics.at[idx, "bankroll"] = prev_bank + pnl

    # Enforce schema for simulations
    SchemaManager.patch_schema(df_metrics, schema_name="simulations")

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        logger.info("Output exists and overwrite=False: %s", out_path)
        return

    if dry_run:
        logger.info(
            "Dry-run: simulated %d steps; would write to %s", len(df_metrics), out_path
        )
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_metrics.to_csv(out_path, index=False)
        logger.info("Simulation written to %s", out_path)


if __name__ == "__main__":
    main()
