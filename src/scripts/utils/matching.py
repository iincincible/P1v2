import pandas as pd
from fuzzywuzzy import fuzz


def load_alias_map(path: str) -> dict:
    df = pd.read_csv(path)
    return dict(zip(df["alias"], df["standard"]))


def apply_alias_map(df: pd.DataFrame, alias_csv: str) -> pd.DataFrame:
    alias_map = load_alias_map(alias_csv)
    df["runner_1"] = df["runner_1"].map(alias_map).fillna(df["runner_1"])
    df["runner_2"] = df["runner_2"].map(alias_map).fillna(df["runner_2"])
    return df


def fuzzy_match_players(df: pd.DataFrame) -> pd.DataFrame:
    def match_names(row):
        if fuzz.ratio(row["runner_1"], row["runner_2"]) > 90:
            return row["runner_1"] + "_A", row["runner_2"] + "_B"
        return row["runner_1"], row["runner_2"]

    df[["runner_1", "runner_2"]] = df.apply(match_names, axis=1, result_type="expand")
    return df


def build_roster_map(sack_df: pd.DataFrame) -> dict:
    """Builds name set for fast lookup during matching"""
    names = set(sack_df["winner_name"]).union(set(sack_df["loser_name"]))
    return {name.lower(): name for name in names}


def resolve_player(name: str, roster_map: dict, alias_map: dict, fuzzy: bool) -> str:
    raw = alias_map.get(name, name).lower()
    if raw in roster_map:
        return roster_map[raw]

    if fuzzy:
        best_match = None
        best_score = 0
        for key in roster_map:
            score = fuzz.ratio(raw, key)
            if score > best_score:
                best_match = key
                best_score = score
        return roster_map.get(best_match) if best_score >= 85 else None

    return None


def match_snapshots_to_results(
    df_matches: pd.DataFrame,
    sackmann_csv: str,
    alias_map: dict = None,
    fuzzy: bool = True
) -> pd.DataFrame:
    """
    Matches Betfair snapshot-based matches to Sackmann match results.
    Adds columns: winner_name, loser_name, player_1_won, round, score, etc.
    """
    if alias_map is None:
        alias_map = {}

    sack_df = pd.read_csv(sackmann_csv)
    roster_map = build_roster_map(sack_df)

    matched = []
    for _, row in df_matches.iterrows():
        p1 = resolve_player(row["runner_1"], roster_map, alias_map, fuzzy)
        p2 = resolve_player(row["runner_2"], roster_map, alias_map, fuzzy)

        if not p1 or not p2:
            matched.append({})
            continue

        candidates = sack_df[
            ((sack_df["winner_name"].isin([p1, p2])) & (sack_df["loser_name"].isin([p1, p2])))
        ]

        if candidates.empty:
            matched.append({})
            continue

        best_match = candidates.iloc[0]
        winner = best_match["winner_name"]
        player_1_won = int(winner == p1)

        matched.append({
            "winner_name": best_match["winner_name"],
            "loser_name": best_match["loser_name"],
            "round": best_match.get("round", ""),
            "score": best_match.get("score", ""),
            "player_1_won": player_1_won,
        })

    df_extra = pd.DataFrame(matched)
    return pd.concat([df_matches.reset_index(drop=True), df_extra], axis=1)
