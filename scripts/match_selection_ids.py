import argparse
import pandas as pd

def clean_name(name):
    return str(name).lower().replace(".", "").replace("-", " ").replace("  ", " ").strip()

def match_with_difflib(player, candidates, threshold=0.8):
    from difflib import get_close_matches
    matches = get_close_matches(player, candidates, n=1, cutoff=threshold)
    return matches[0] if matches else None

def match_with_fuzzywuzzy(player, candidates, threshold=90):
    from fuzzywuzzy import process
    match, score = process.extractOne(player, candidates)
    return match if score >= threshold else None

def match_with_rapidfuzz(player, candidates, threshold=90):
    from rapidfuzz import fuzz, process
    match = process.extractOne(player, candidates, scorer=fuzz.WRatio)
    return match[0] if match and match[1] >= threshold else None

def match_ids(df, snaps_df, method, fuzzy_threshold):
    df["player_1_clean"] = df["player_1"].apply(clean_name)
    df["player_2_clean"] = df["player_2"].apply(clean_name)
    snaps_df["runner_clean"] = snaps_df["runner_name"].apply(clean_name)

    ref = snaps_df.dropna(subset=["market_id", "runner_clean", "selection_id"]).drop_duplicates(
        subset=["market_id", "runner_clean"]
    )

    def get_selection_ids(row):
        subset = ref[ref["market_id"] == row["market_id"]]
        candidates = subset["runner_clean"].tolist()

        sid1 = sid2 = None

        if method == "exact":
            sid1 = subset.loc[subset["runner_clean"] == row["player_1_clean"], "selection_id"].squeeze()
            sid2 = subset.loc[subset["runner_clean"] == row["player_2_clean"], "selection_id"].squeeze()
        elif method == "difflib":
            m1 = match_with_difflib(row["player_1_clean"], candidates, fuzzy_threshold)
            m2 = match_with_difflib(row["player_2_clean"], candidates, fuzzy_threshold)
            sid1 = subset.loc[subset["runner_clean"] == m1, "selection_id"].squeeze() if m1 else None
            sid2 = subset.loc[subset["runner_clean"] == m2, "selection_id"].squeeze() if m2 else None
        elif method == "fuzzywuzzy":
            m1 = match_with_fuzzywuzzy(row["player_1_clean"], candidates, int(fuzzy_threshold * 100))
            m2 = match_with_fuzzywuzzy(row["player_2_clean"], candidates, int(fuzzy_threshold * 100))
            sid1 = subset.loc[subset["runner_clean"] == clean_name(m1), "selection_id"].squeeze() if m1 else None
            sid2 = subset.loc[subset["runner_clean"] == clean_name(m2), "selection_id"].squeeze() if m2 else None
        elif method == "jaro_winkler":
            m1 = match_with_rapidfuzz(row["player_1_clean"], candidates, int(fuzzy_threshold * 100))
            m2 = match_with_rapidfuzz(row["player_2_clean"], candidates, int(fuzzy_threshold * 100))
            sid1 = subset.loc[subset["runner_clean"] == clean_name(m1), "selection_id"].squeeze() if m1 else None
            sid2 = subset.loc[subset["runner_clean"] == clean_name(m2), "selection_id"].squeeze() if m2 else None
        else:
            raise ValueError(f"Invalid matching method: {method}")

        return pd.Series([sid1, sid2])

    df[["selection_id_1", "selection_id_2"]] = df.apply(get_selection_ids, axis=1)

    matched = df["selection_id_1"].notna().sum()
    total = len(df)
    print(f"✅ Matched selection IDs for {matched}/{total} rows ({matched / total:.1%})")

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--method", choices=["exact", "difflib", "fuzzywuzzy", "jaro_winkler"], default="jaro_winkler")
    parser.add_argument("--fuzzy_threshold", type=float, default=0.8)
    args = parser.parse_args()

    df = pd.read_csv(args.merged_csv)
    snaps_df = pd.read_csv(args.snapshots_csv)

    required_cols = {"player_1", "player_2", "market_id"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"❌ merged_csv missing required columns: {required_cols}")

    if "runner_name" not in snaps_df.columns or "selection_id" not in snaps_df.columns:
        raise ValueError("❌ snapshots_csv must contain 'runner_name' and 'selection_id' columns")

    df_patched = match_ids(df, snaps_df, args.method, args.fuzzy_threshold)
    df_patched.to_csv(args.output_csv, index=False)
    print(f"📁 Saved patched file to: {args.output_csv}")

if __name__ == "__main__":
    main()
