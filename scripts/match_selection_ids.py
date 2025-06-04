import argparse
import pandas as pd
from rapidfuzz import fuzz
from tqdm import tqdm

def normalize_name(name):
    return str(name).lower().replace(".", "").replace("-", " ").replace(",", "").strip()

def token_overlap_match(player_name, candidates, min_token_match=2):
    tokens = set(normalize_name(player_name).split())
    for cand in candidates:
        cand_tokens = set(normalize_name(cand).split())
        if len(tokens & cand_tokens) >= min(min_token_match, len(tokens)):
            return cand
    return None

def match_ids(df, snaps_df, threshold=85):
    df["player_1_clean"] = df["player_1"].apply(normalize_name)
    df["player_2_clean"] = df["player_2"].apply(normalize_name)
    snaps_df["runner_clean"] = snaps_df["runner_name"].apply(normalize_name)

    ref = snaps_df.dropna(subset=["market_id", "runner_clean", "selection_id"]).drop_duplicates(
        subset=["market_id", "runner_clean"]
    )

    selection_id_1 = []
    selection_id_2 = []

    tqdm.pandas(desc="🔍 Matching IDs with fallback")

    for _, row in df.iterrows():
        subset = ref[ref["market_id"] == row["market_id"]]
        candidates = subset["runner_clean"].tolist()
        sid1 = sid2 = None

        # Try exact match first
        if row["player_1_clean"] in candidates:
            sid1 = subset.loc[subset["runner_clean"] == row["player_1_clean"], "selection_id"].squeeze()
        if row["player_2_clean"] in candidates:
            sid2 = subset.loc[subset["runner_clean"] == row["player_2_clean"], "selection_id"].squeeze()

        # Try fuzzy fallback (Jaro-Winkler)
        if pd.isna(sid1):
            best = max(candidates, key=lambda c: fuzz.WRatio(row["player_1_clean"], c), default=None)
            if best and fuzz.WRatio(row["player_1_clean"], best) >= threshold:
                sid1 = subset.loc[subset["runner_clean"] == best, "selection_id"].squeeze()

        if pd.isna(sid2):
            best = max(candidates, key=lambda c: fuzz.WRatio(row["player_2_clean"], c), default=None)
            if best and fuzz.WRatio(row["player_2_clean"], best) >= threshold:
                sid2 = subset.loc[subset["runner_clean"] == best, "selection_id"].squeeze()

        # Final fallback: token containment
        if pd.isna(sid1):
            match = token_overlap_match(row["player_1"], subset["runner_name"].tolist())
            if match:
                match_clean = normalize_name(match)
                sid1 = subset.loc[subset["runner_clean"] == match_clean, "selection_id"].squeeze()

        if pd.isna(sid2):
            match = token_overlap_match(row["player_2"], subset["runner_name"].tolist())
            if match:
                match_clean = normalize_name(match)
                sid2 = subset.loc[subset["runner_clean"] == match_clean, "selection_id"].squeeze()

        selection_id_1.append(sid1)
        selection_id_2.append(sid2)

    df["selection_id_1"] = selection_id_1
    df["selection_id_2"] = selection_id_2
    matched = df["selection_id_1"].notna().sum()
    print(f"✅ Matched selection IDs for {matched}/{len(df)} rows")
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--fuzzy_threshold", type=int, default=85)
    args = parser.parse_args()

    df = pd.read_csv(args.merged_csv)
    snaps_df = pd.read_csv(args.snapshots_csv)

    required_cols = {"player_1", "player_2", "market_id"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"❌ merged_csv missing required columns: {required_cols}")

    if "runner_name" not in snaps_df.columns or "selection_id" not in snaps_df.columns:
        raise ValueError("❌ snapshots_csv must contain 'runner_name' and 'selection_id' columns")

    df_patched = match_ids(df, snaps_df, args.fuzzy_threshold)
    df_patched.to_csv(args.output_csv, index=False)
    print(f"📁 Saved patched file to: {args.output_csv}")

if __name__ == "__main__":
    main()
