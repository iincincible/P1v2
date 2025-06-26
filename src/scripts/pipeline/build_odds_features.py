import pandas as pd
import numpy as np
from pathlib import Path
from scripts.utils.cli import guarded_run
from scripts.utils.logger import setup_logging, log_info, log_warning
from scripts.utils.schema import SchemaManager


@guarded_run
def main(
    input_csv: str,
    output_csv: str,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Build odds-derived features for each match.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    in_path = Path(input_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")
    out_path = Path(output_csv)
    if out_path.exists() and not overwrite:
        log_info(f"Output exists and overwrite=False: {out_path}")
        return

    df = pd.read_csv(in_path)
    log_info(f"Loaded {len(df)} rows from {in_path}")

    # Feature engineering: implied probabilities and margin
    if "ltp_player_1" in df.columns and "ltp_player_2" in df.columns:
        df["ltp_player_1"] = pd.to_numeric(df["ltp_player_1"], errors="coerce")
        df["ltp_player_2"] = pd.to_numeric(df["ltp_player_2"], errors="coerce")
        df["implied_prob_1"] = 1 / df["ltp_player_1"].replace(0, np.nan)
        df["implied_prob_2"] = 1 / df["ltp_player_2"].replace(0, np.nan)
        df["implied_prob_diff"] = df["implied_prob_1"] - df["implied_prob_2"]
        df["odds_margin"] = df["implied_prob_1"] + df["implied_prob_2"]
        log_info("Added implied probability and margin features.")
    else:
        for col in [
            "implied_prob_1",
            "implied_prob_2",
            "implied_prob_diff",
            "odds_margin",
        ]:
            df[col] = np.nan
        log_warning(
            "Missing 'ltp_player_1' or 'ltp_player_2'; filled feature columns with NaN."
        )

    if df[["implied_prob_1", "implied_prob_2"]].isnull().any().any():
        log_warning(
            "Some implied probabilities are NaN (possibly due to missing or zero LTPs)."
        )

    df_out = SchemaManager.patch_schema(df, schema_name="features")
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(out_path, index=False)
        log_info(f"Features written to {out_path}")


if __name__ == "__main__":
    main()
