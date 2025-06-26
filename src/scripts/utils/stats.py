import numpy as np


def safe_mean(x):
    if len(x) == 0:
        return np.nan
    return np.mean(x)
