import pandas as pd
from pathlib import Path
from scripts.utils.logger import log_info
from scripts.utils.value_metrics import compute_value_metrics
from scripts.utils.schema import normalize_columns, enforce_schema


def run_simulate_bankroll_growth(
    df: pd.DataFrame,
    initial_bankroll: float = 1000.0,
) -> pd.DataFrame:
    """
    Simulate bankroll growth given value bet DataFrame and initial bankroll.
    """
    df = normalize_columns(df)
    df_metrics = compute_value_metrics(df)
    df_metrics = df_metrics.copy()
    df_metrics.insert(0, "bankroll", initial_bankroll)
    for idx in df_metrics.index[1:]:
        prev_bank = df_metrics.at[idx - 1, "bankroll"]
        kelly = df_metrics.at[idx - 1, "kelly_fraction"]
        bet_amount = prev_bank * kelly
        outcome = df_metrics.at[idx - 1, "winner"]
        odds = df_metrics.at[idx - 1, "odds"]
        pnl = bet_amount * (odds - 1) * outcome - bet_amount * (1 - outcome)
        df_metrics.at[idx, "bankroll"] = prev_bank + pnl
    return enforce_schema(df_metrics, schema_name="simulations")


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Simulate bankroll growth from value bets"
    )
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--initial_bankroll", type=float, default=1000.0)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.input_csv)
    log_info(f"Loaded {len(df)} bets from {args.input_csv}")
    df_out = run_simulate_bankroll_growth(df, initial_bankroll=args.initial_bankroll)
    out_path = Path(args.output_csv)
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Simulation written to {out_path}")


if __name__ == "__main__":
    main_cli()
