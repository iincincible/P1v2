# File: src/scripts/modeling/train_eval_model.py

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.cli_utils import (
    add_common_flags,
    assert_file_exists,
    output_file_guard,
)
from scripts.utils.logger import log_error, log_info, log_success
from scripts.utils.normalize_columns import (
    normalize_columns,
    patch_winner_column,
    enforce_canonical_columns,
)

logging.basicConfig(level=logging.INFO)


@output_file_guard(output_arg="output_model")
def train_eval_model(
    input_files,
    output_model,
    algorithm="rf",
    test_size=0.25,
    random_state=42,
    overwrite=False,
    dry_run=False,
):
    all_dfs = []
    for path in input_files:
        try:
            assert_file_exists(path, "input_csv")
            df = pd.read_csv(path)
            df = normalize_columns(df)
            df = patch_winner_column(df)
            enforce_canonical_columns(df, context=path)
            all_dfs.append(df)
            log_info(f"✅ Loaded and validated {len(df)} rows from {path}")
        except Exception as e:
            log_error(f"❌ Skipping {path}: {e}")

    if not all_dfs:
        raise ValueError("❌ No valid data to train on after preprocessing.")

    df = pd.concat(all_dfs, ignore_index=True)
    log_success(f"📊 Combined dataset contains {len(df)} rows")

    # Infer feature columns: numeric columns excluding label and group identifiers
    excluded = {"winner", "match_id"}
    feature_cols = [
        c
        for c in df.columns
        if c not in excluded and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not feature_cols:
        raise ValueError("❌ No numeric feature columns found after preprocessing.")
    log_info(f"🛠 Using features: {feature_cols}")

    X = df[feature_cols]
    y = df["winner"]
    if "match_id" not in df.columns:
        raise ValueError(
            "❌ 'match_id' column is required for grouped train/test split."
        )
    groups = df["match_id"]

    # Group-aware train/test split to prevent leakage
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    log_success(f"🔀 Split into {len(train_idx)} train and {len(test_idx)} test rows")

    # Choose and train model
    if algorithm.lower() in {"rf", "random_forest"}:
        model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    elif algorithm.lower() in {"lr", "logistic_regression"}:
        model = LogisticRegression(max_iter=1000, random_state=random_state)
    else:
        raise ValueError(f"❌ Unsupported algorithm: {algorithm}")
    log_info(f"🚀 Training {algorithm} model")
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    proba = (
        model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    )
    report = classification_report(y_test, preds, digits=4)
    log_info("📈 Classification Report:\n" + report)
    if proba is not None:
        auc = roc_auc_score(y_test, proba)
        log_info(f"🔍 ROC AUC: {auc:.4f}")

    # Save model
    out_path = Path(output_model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_path)
    log_success(f"✅ Saved trained model to {output_model}")

    # Save metadata
    meta = {
        "timestamp": datetime.now().isoformat(),
        "model_type": algorithm,
        "features": feature_cols,
        "test_size": test_size,
        "random_state": random_state,
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "input_files": input_files,
    }
    meta_path = out_path.with_suffix(".json")
    with open(meta_path, "w") as mf:
        json.dump(meta, mf, indent=2)
    log_success(f"📄 Saved metadata to {meta_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Train main evaluation model (no leakage)."
    )
    parser.add_argument(
        "--input_files",
        nargs="+",
        required=True,
        help="One or more CSVs containing precomputed features and actual_winner.",
    )
    parser.add_argument(
        "--output_model",
        required=True,
        help="Path to write the trained model (joblib format).",
    )
    parser.add_argument(
        "--algorithm",
        choices=["rf", "random_forest", "lr", "logistic_regression"],
        default="rf",
        help="Which model to train.",
    )
    parser.add_argument(
        "--test_size",
        type=float,
        default=0.25,
        help="Fraction of data to hold out for testing.",
    )
    parser.add_argument(
        "--random_state", type=int, default=42, help="Random seed for reproducibility."
    )
    add_common_flags(parser)
    args = parser.parse_args()

    train_eval_model(
        input_files=args.input_files,
        output_model=args.output_model,
        algorithm=args.algorithm,
        test_size=args.test_size,
        random_state=args.random_state,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
