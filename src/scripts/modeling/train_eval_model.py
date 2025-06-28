import json
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.logger import log_info, log_success
from scripts.utils.schema import normalize_columns, patch_winner_column, enforce_schema


def run_train_eval_model(
    dfs: list[pd.DataFrame],
    algorithm: str = "rf",
    test_size: float = 0.25,
    random_state: int = 42,
) -> tuple:
    """
    Train a classification model on value bets and evaluate.
    Returns (model, report, auc, meta_dict).
    """
    all_dfs = []
    for df in dfs:
        df = normalize_columns(df)
        df = patch_winner_column(df)
        enforce_schema(df, "value_bets")
        all_dfs.append(df)
    if not all_dfs:
        raise ValueError("No valid data to train on after preprocessing.")
    df = pd.concat(all_dfs, ignore_index=True)
    excluded = {"winner", "match_id"}
    feature_cols = [
        c
        for c in df.columns
        if c not in excluded and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not feature_cols:
        raise ValueError("No numeric feature columns found after preprocessing.")
    X = df[feature_cols]
    y = df["winner"]
    if "match_id" not in df.columns:
        raise ValueError("'match_id' column is required for grouped train/test split.")
    groups = df["match_id"]
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    if algorithm == "rf":
        model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    elif algorithm == "logreg":
        model = LogisticRegression(max_iter=500, random_state=random_state)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = (
        model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    )
    auc = roc_auc_score(y_test, y_prob) if y_prob is not None else None
    report = classification_report(y_test, y_pred, digits=3, output_dict=False)
    meta = {
        "timestamp": datetime.now().isoformat(),
        "model_type": type(model).__name__,
        "features": feature_cols,
        "algorithm": algorithm,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "auc": auc,
    }
    return model, report, auc, meta


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Train and evaluate a model on value bets"
    )
    parser.add_argument(
        "--input_files", required=True, help="Space-separated list of CSVs"
    )
    parser.add_argument("--output_model", required=True)
    parser.add_argument("--algorithm", choices=["rf", "logreg"], default="rf")
    parser.add_argument("--test_size", type=float, default=0.25)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    files = args.input_files.split()
    dfs = [pd.read_csv(path) for path in files]
    model, report, auc, meta = run_train_eval_model(
        dfs, algorithm=args.algorithm, test_size=args.test_size
    )
    log_info(f"Evaluation on holdout set (AUC={auc:.3f}):")
    log_info("\n" + str(report))
    output_path = Path(args.output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        joblib.dump(model, output_path)
        log_success(f"Saved model to {args.output_model}")
        with open(output_path.with_suffix(".json"), "w") as f:
            json.dump(meta, f, indent=2)
        log_success(f"Saved metadata to {output_path.with_suffix('.json')}")


if __name__ == "__main__":
    main_cli()
