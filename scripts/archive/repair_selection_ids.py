import pandas as pd
import argparse
from fuzzywuzzy import process

def repair_selection_ids(merged_csv, snapshots_csv, output_csv, fuzzy_threshold=90):
    df = pd.read_csv(merged_csv)
    snaps = pd.read_csv(snapshots_csv)

    # Clean name fields for matching
    df["player_1_lc"] = df["player_1"].str.lower().str.replace(".", "", regex=False).str.strip()
    df["player_2_lc"] = df["player_2"].str.lower().str.replace(".", "", regex=False).str.strip()
    snaps["runner_name_lc"] = snaps["runner_name"].str.lower().str.replace(".", "", regex=False).str.strip()

    # Build reference table: (market_id, runner_name_lc) → selection_id
    ref = snaps.drop_duplicates(subset=["market_id", "runner_name_lc"])[["market_id", "runner_name_lc", "selection_id"]]

    # Define matching function
    def match_selection_ids(row):
        market_id = row["market_id"]
        p1, p2 = row["player_1_lc"], row["player_2_lc"]
        subset = ref[ref["market_id"] == market_id]

        sid1 = sid2 = None

        if not subset.empty:
            choices = subset["runner_name_lc"].tolist()

            if p1 in choices:
                sid1 = subset.loc[subset["runner_name_lc"] == p1, "selection_id"].values[0]
            else:
                match, score = process.extractOne(p1, choices)
                if score >= fuzzy_threshold:
                    sid1 = subset.loc[subset["runner_name_lc"] == match, "selection_id"].values[0]

            if p2 in choices:
                sid2 = subset.loc[subset["runner_name_lc"] == p2, "selection_id"].values[0]
            else:
                match, score = process.extractOne(p2, choices)
                if score >= fuzzy_threshold:
                    sid2 = subset.loc[subset["runner_name_lc"] == match, "selection_id"].values[0]

        return pd.Series([sid1, sid2], index=["selection_id_1", "selection_id_2"])

    # Apply fuzzy matching
    df[["selection_id_1", "selection_id_2"]] = df.apply(match_selection_ids, axis=1)

    # Save
    df.to_csv(output_csv, index=False)

    matched = df["selection_id_1"].notna().sum()
    total = len(df)
    print(f"✅ Repaired selection IDs → saved to {output_csv}")
    print(f"🔍 Matched {matched} of {total} rows ({matched / total:.1%})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--snapshots_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    repair_selection_ids(args.merged_csv, args.snapshots_csv, args.output_csv)
