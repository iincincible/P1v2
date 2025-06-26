import numpy as np


def compute_value_metrics(df):
    df = df.copy()
    # Expected value: (prob * odds - (1 - prob)) for each bet
    if "predicted_prob" in df.columns and "odds" in df.columns:
        df["expected_value"] = df["predicted_prob"] * df["odds"] - (
            1 - df["predicted_prob"]
        )
    # Kelly fraction: max(0, (prob * (odds-1) - (1 - prob)) / (odds-1))
    if "predicted_prob" in df.columns and "odds" in df.columns:
        with np.errstate(divide="ignore", invalid="ignore"):
            numer = df["predicted_prob"] * (df["odds"] - 1) - (1 - df["predicted_prob"])
            denom = df["odds"] - 1
            kelly = np.where(denom > 0, numer / denom, 0.0)
            df["kelly_fraction"] = np.maximum(0, kelly)
    return df
