import pandas as pd

df = pd.read_csv("data/processed/ausopen_2023_atp_predictions.csv")
rows = []
for _, row in df.iterrows():
    # Player 1 bet
    rows.append(
        {
            "player_1": row["player_1"],
            "player_2": row["player_2"],
            "odds": row["ltp_player_1"],
            "match_id": row["match_id"],
            "market_id": row["market_id"],
            "implied_prob_1": row["implied_prob_1"],
            "implied_prob_2": row["implied_prob_2"],
            "implied_prob_diff": row["implied_prob_diff"],
            "odds_margin": row["odds_margin"],
        }
    )
    # Player 2 bet
    rows.append(
        {
            "player_1": row["player_2"],
            "player_2": row["player_1"],
            "odds": row["ltp_player_2"],
            "match_id": row["match_id"],
            "market_id": row["market_id"],
            "implied_prob_1": row["implied_prob_2"],  # swap
            "implied_prob_2": row["implied_prob_1"],  # swap
            "implied_prob_diff": -row["implied_prob_diff"],  # swap
            "odds_margin": row["odds_margin"],
        }
    )

out = pd.DataFrame(rows)
out.to_csv("data/processed/ausopen_2023_atp_bet_candidates.csv", index=False)
print("Saved: data/processed/ausopen_2023_atp_bet_candidates.csv")
