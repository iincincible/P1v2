import numpy as np


def add_ev_and_kelly(df):
    """
    Add expected value and Kelly fraction columns to a DataFrame.
    """
    df = df.copy()
    if "predicted_prob" in df.columns and "odds" in df.columns:
        # EV = p*odds - (1-p)
        df["expected_value"] = df["predicted_prob"] * df["odds"] - (
            1 - df["predicted_prob"]
        )
        # Kelly: max(0, (p*(odds-1) - (1-p)) / (odds-1))
        numer = df["predicted_prob"] * (df["odds"] - 1) - (1 - df["predicted_prob"])
        denom = df["odds"] - 1
        with np.errstate(divide="ignore", invalid="ignore"):
            df["kelly_fraction"] = np.where(denom > 0, numer / denom, 0.0)
        df["kelly_fraction"] = np.maximum(0, df["kelly_fraction"])
    else:
        df["expected_value"] = np.nan
        df["kelly_fraction"] = np.nan
    return df
