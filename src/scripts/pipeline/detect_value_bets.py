import pandas as pd
from pathlib import Path
from scripts.utils.cli import guarded_run
from scripts.utils.logger import setup_logging, log_info, log_warning
from scripts.utils.schema import SchemaManager
from scripts.utils.constants import DEFAULT_MAX_MARGIN
from scripts.utils.value_metrics import compute_value_metrics


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    ev_threshold: float = 0.2,
    confidence_threshold: float = 0.4,
    max_odds: float = 6.0,
    max_margin: float = DEFAULT_MAX_MARGIN,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Identify value bets based on expected value and confidence thresholds.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    in_path = Path(input_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")
    df = pd.read_csv(in_path)
    log_info(f"Loaded {len(df)} rows from {in_path}")

    if "expected_value" not in df.columns or "kelly_fraction" not in df.columns:
        df = compute_value_metrics(df)

    if "confidence_score" not in df.columns and "predicted_prob" in df.columns:
        df["confidence_score"] = df["predicted_prob"]

    mask = (
        (df["expected_value"] >= ev_threshold)
        & (df["confidence_score"] >= confidence_threshold)
        & (df["odds"] <= max_odds)
    )
    if "odds_margin" in df.columns:
        mask &= df["odds_margin"] <= max_margin

    df_filtered = df[mask]
    if df_filtered.empty:
        log_warning("No value bets found after filtering.")
        df_out = pd.DataFrame(columns=SchemaManager._schemas["value_bets"]["order"])
        df_out = SchemaManager.patch_schema(df_out, "value_bets")
    else:
        df_out = SchemaManager.patch_schema(df_filtered, "value_bets")
        log_info(f"Filtered {len(df_filtered)} of {len(df)} value bets.")

    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Value bets written to {out_path}")


if __name__ == "__main__":
    main()
