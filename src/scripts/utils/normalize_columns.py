import re
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names:
      - strip whitespace, lowercase, replace spaces with underscores
      - runner_{n} → player_{n} for any n
      - merge all odds_* columns into a single 'odds' column, taking the
        first non-null per row
      - rename simple aliases:
          prob            → predicted_prob
          ev              → expected_value
          actual_winner   → winner
      - reorder so that player_ columns come first, in numeric order
    """
    df = df.copy()
    # 1) Basic cleanup: strip, lowercase, underscores
    cleaned = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.columns = cleaned

    # 2) Runner → Player mapping via regex
    runner_map = {}
    for col in df.columns:
        m = re.match(r"runner_(\d+)$", col)
        if m:
            runner_map[col] = f"player_{m.group(1)}"
    if runner_map:
        df = df.rename(columns=runner_map)

    # 3) Simple aliases
    simple_aliases = {
        "prob": "predicted_prob",
        "ev": "expected_value",
        "actual_winner": "winner",
    }
    existing_aliases = {k: v for k, v in simple_aliases.items() if k in df.columns}
    if existing_aliases:
        df = df.rename(columns=existing_aliases)

    # 4) Merge odds_* columns into one 'odds'
    odds_cols = [c for c in df.columns if c.startswith("odds_")]
    if odds_cols:
        # bfill across columns and select first non-null per row
        df["odds"] = df[odds_cols].bfill(axis=1).iloc[:, 0]
        df = df.drop(columns=odds_cols)

    # 5) Reorder: player_1, player_2, … then the rest in original order
    player_cols = sorted(
        [c for c in df.columns if c.startswith("player_")],
        key=lambda x: int(x.split("_")[1]),
    )
    other_cols = [c for c in df.columns if c not in player_cols]
    df = df[player_cols + other_cols]

    return df
