import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.cli import guarded_run
from scripts.utils.logger import setup_logging, log_info, log_success, log_error
from scripts.utils.normalize_columns import (
    normalize_and_patch_canonical_columns,
    patch_winner_column,
    enforce_canonical_columns,
)


@guarded_run
def main(
    input_files: str,  # Space-separated list of files
    output_model: str,
    algorithm: str = "rf",
    test_size: float = 0.25,
    random_state: int = 42,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    json_logs: bool = False,
):
    """
    Train main evaluation model (no data leakage).
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_logs=json_logs)
    files = input_files.split()
    all_dfs = []
    for path in files:
        try:
            df = pd.read_csv(path)
            df = normalize_and_patch_canonical_columns(df, context=path)
            df = patch_winner_column(df)
            enforce_canonical_columns(df, context=path)
            all_dfs.append(df)
            log_info(f"Loaded and validated {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"Skipping {path}: {e}")

    if not all_dfs:
        raise ValueError("No valid data to train on after preprocessing.")

    df = pd.concat(all_dfs, ignore_index=True)
    log_success(f"Combined dataset contains {len(df)} rows")

    excluded = {"winner", "match_id"}
    feature_cols = [
        c
        for c in df.columns
        if c not in excluded and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not feature_cols:
        raise ValueError("No numeric feature columns found after preprocessing.")
    log_info(f"Using features: {feature_cols}")

    X = df[feature_cols]
    y = df["winner"]
    if "match_id" not in df.columns:
        raise ValueError("'match_id' column is required for grouped train/test split.")
    groups = df["match_id"]

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    log_success(f"Split into {len(train_idx)} train and {len(test_idx)} test rows")

    if algorithm.lower() in {"rf", "random_forest"}:
        model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    elif algorithm.lower() in {"lr", "logistic_regression"}:
        model = LogisticRegression(max_iter=1000, random_state=random_state)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    log_info(f"Training {algorithm} model")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    proba = (
        model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    )
    report = classification_report(y_test, preds, digits=4)
    log_info("Classification Report:\n" + report)
    if proba is not None:
        auc = roc_auc_score(y_test, proba)
        log_info(f"ROC AUC: {auc:.4f}")

    out_path = Path(output_model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        joblib.dump(model, out_path)
        log_success(f"Saved trained model to {output_model}")

        meta = {
            "timestamp": datetime.now().isoformat(),
            "model_type": algorithm,
            "features": feature_cols,
            "test_size": test_size,
            "random_state": random_state,
            "train_rows": int(len(train_idx)),
            "test_rows": int(len(test_idx)),
            "input_files": files,
        }
        meta_path = out_path.with_suffix(".json")
        with open(meta_path, "w") as mf:
            json.dump(meta, mf, indent=2)
        log_success(f"Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
