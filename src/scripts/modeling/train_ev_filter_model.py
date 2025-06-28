import json
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit

from scripts.utils.logger import log_info, log_success
from scripts.utils.schema import normalize_columns, patch_winner_column, enforce_schema
from scripts.utils.constants import DEFAULT_EV_THRESHOLD


def run_train_ev_filter_model(
    dfs: list[pd.DataFrame],
    min_ev: float = DEFAULT_EV_THRESHOLD,
    random_state: int = 42,
) -> tuple:
    """
    Train a RandomForestClassifier to filter value bets above EV threshold.
    Returns (model, report, meta_dict).
    """
    all_rows = []
    for df in dfs:
        df = normalize_columns(df)
        df = patch_winner_column(df)
        df = df[df["expected_value"] >= min_ev]
        all_rows.append(df)
    if not all_rows:
        raise ValueError("No valid input data found after filtering.")
    df = pd.concat(all_rows, ignore_index=True)
    enforce_schema(df, "value_bets")
    features = ["predicted_prob", "odds", "expected_value"]
    X = df[features]
    y = df["winner"]
    if "match_id" not in df.columns:
        raise ValueError("'match_id' column required for grouped splitting")
    groups = df["match_id"]
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    model.fit(X_train, y_train)
    report = classification_report(
        y_test, model.predict(X_test), digits=3, output_dict=False
    )
    meta = {
        "timestamp": datetime.now().isoformat(),
        "model_type": "RandomForestClassifier",
        "features": features,
        "ev_threshold": min_ev,
        "train_rows": len(df),
    }
    return model, report, meta


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Train EV filter model")
    parser.add_argument(
        "--input_files", required=True, help="Space-separated list of CSVs"
    )
    parser.add_argument("--output_model", required=True)
    parser.add_argument("--min_ev", type=float, default=DEFAULT_EV_THRESHOLD)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json_logs", action="store_true")
    args = parser.parse_args()
    files = args.input_files.split()
    dfs = [pd.read_csv(path) for path in files]
    model, report, meta = run_train_ev_filter_model(dfs, min_ev=args.min_ev)
    log_info("Evaluation on holdout set:")
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
