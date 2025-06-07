import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path

from scripts.utils.cli_utils import should_run, assert_file_exists, add_common_flags
from scripts.utils.selection import build_market_runner_map
from scripts.utils.logger import log_info, log_warning, log_error, log_success


def main():
    parser = argparse.ArgumentParser(description="Merge final LTP odds into match rows.")
    parser.add_argument("--match_csv", required=True, help="Path to match-level input CSV")
    parser.add_argument("--snapshots_csv", required=True, help="Path to parsed Betfair snapshots")
    parser.add_argument("--output_csv", required=True, help="Path to save merged output")
    add_common_flags(parser)
    args = parser.parse_args()

    output_path = Path(args.output_csv)

    if not should_run(output_path, args.overwrite, args.dry_run):
        return

    assert_file_exists(args.match_csv, "match_csv")
    assert_file_exists(args.snapshots_csv, "snapshots_csv")

    df_matches = pd.read_csv(args.match_csv)
    df_snaps = pd.read_csv(args.snapshots_csv)

    if "match_id" not in df_matches.columns:
        log_error("❌ match_id missing in match_csv")
        raise ValueError("match_id is required in match_csv for downstream tracking.")

    df_snaps["market_id"] = df_snaps["market_id"].astype(str)
    df_snaps["selection_id"] = df_snaps["selection_id"].astype(str)

    market_runner_map = build_market_runner_map(df_snaps)

    odds_1 = []
    odds_2 = []
    missing = 0

    for _, row in tqdm(df_matches.iterrows(), total=len(df_matches), desc="Merging LTPs"):
        market_id = str(row["market_id"])
        sel1 = str(row.get("selection_id_1", ""))
        sel2 = str(row.get("selection_id_2", ""))
        market = market_runner_map.get(market_id, {})

        o1 = df_snaps.loc[
            (df_snaps["market_id"] == market_id) & (df_snaps["selection_id"] == sel1),
            "ltp"
        ].values
        o2 = df_snaps.loc[
            (df_snaps["market_id"] == market_id) & (df_snaps["selection_id"] == sel2),
            "ltp"
        ].values

        val1 = o1[0] if len(o1) else None
        val2 = o2[0] if len(o2) else None

        if pd.isna(val1) or pd.isna(val2):
            missing += 1
        odds_1.append(val1)
        odds_2.append(val2)

    df_matches["odds_player_1"] = odds_1
    df_matches["odds_player_2"] = odds_2

    log_success(f"✅ Matched {len(df_matches) - missing} LTP entries; unmatched: {missing}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_matches.to_csv(output_path, index=False)
    log_success(f"✅ Saved merged odds to {output_path}")


if __name__ == "__main__":
    main()
