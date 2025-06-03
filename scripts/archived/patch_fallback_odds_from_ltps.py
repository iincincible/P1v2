import pandas as pd
import argparse

def patch_fallback_odds(merged_csv, ltps_csv, output_csv):
    df = pd.read_csv(merged_csv)
    ltps = pd.read_csv(ltps_csv)

    # Player 1 fallback
    odds1 = df[["market_id", "selection_id_1", "odds_player_1"]].copy()
    odds1 = odds1.merge(
        ltps.rename(columns={"selection_id": "selection_id_1", "ltp": "ltp_1"}),
        on=["market_id", "selection_id_1"],
        how="left"
    )
    recovered_p1 = odds1["odds_player_1"].isna() & odds1["ltp_1"].notna()
    odds1["odds_player_1"] = odds1["odds_player_1"].fillna(odds1["ltp_1"])

    # Player 2 fallback
    odds2 = df[["market_id", "selection_id_2", "odds_player_2"]].copy()
    odds2 = odds2.merge(
        ltps.rename(columns={"selection_id": "selection_id_2", "ltp": "ltp_2"}),
        on=["market_id", "selection_id_2"],
        how="left"
    )
    recovered_p2 = odds2["odds_player_2"].isna() & odds2["ltp_2"].notna()
    odds2["odds_player_2"] = odds2["odds_player_2"].fillna(odds2["ltp_2"])

    # Update main df
    df["odds_player_1"] = odds1["odds_player_1"]
    df["odds_player_2"] = odds2["odds_player_2"]

    # Save
    df.to_csv(output_csv, index=False)

    print(f"✅ Fallback odds patched → saved to {output_csv}")
    print(f"🩹 Recovered odds_player_1: {recovered_p1.sum()}")
    print(f"🩹 Recovered odds_player_2: {recovered_p2.sum()}")
    print(f"🧾 Rows with any odds: {(df[['odds_player_1', 'odds_player_2']].notna().any(axis=1)).sum()} of {len(df)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged_csv", required=True)
    parser.add_argument("--ltps_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    patch_fallback_odds(args.merged_csv, args.ltps_csv, args.output_csv)
