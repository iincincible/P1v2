import pandas as pd
from pathlib import Path
from scripts.utils.cli import guarded_run
from scripts.utils.logger import setup_logging, log_info
from scripts.utils.value_metrics import compute_value_metrics
from scripts.utils.schema import SchemaManager


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    initial_bankroll: float = 1000.0,
    dry_run: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Simulate bankroll growth over a series of value bets, using Kelly staking.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    in_path = Path(input_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")

    df = pd.read_csv(in_path)
    log_info(f"Loaded {len(df)} bets from {in_path}")

    df_metrics = compute_value_metrics(df)
    df_metrics.insert(0, "bankroll", initial_bankroll)

    for idx in df_metrics.index[1:]:
        prev_bank = df_metrics.at[idx - 1, "bankroll"]
        kelly = df_metrics.at[idx - 1, "kelly_fraction"]
        bet_amount = prev_bank * kelly
        outcome = df_metrics.at[idx - 1, "result"]
        odds = df_metrics.at[idx - 1, "odds"]
        pnl = bet_amount * (odds - 1) * outcome - bet_amount * (1 - outcome)
        df_metrics.at[idx, "bankroll"] = prev_bank + pnl

    SchemaManager.patch_schema(df_metrics, schema_name="simulations")

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_metrics.to_csv(out_path, index=False)
        log_info(f"Simulation written to {out_path}")


if __name__ == "__main__":
    main()
