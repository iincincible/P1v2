class SchemaManager:
    _schemas = {
        "matches": {
            "order": ["match_id", "player_1", "player_2", "scheduled_time", "market_id"]
        },
        "matches_with_ids": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "selection_id_1",
                "selection_id_2",
            ]
        },
        "features": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "ltp_player_1",
                "ltp_player_2",
                "implied_prob_1",
                "implied_prob_2",
                "implied_prob_diff",
                "odds_margin",
            ]
        },
        "predictions": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "implied_prob_1",
                "implied_prob_2",
                "implied_prob_diff",
                "odds_margin",
                "predicted_prob",
            ]
        },
        "value_bets": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "odds",
                "predicted_prob",
                "expected_value",
                "kelly_fraction",
                "confidence_score",
                "winner",
            ]
        },
        "simulations": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "odds",
                "predicted_prob",
                "expected_value",
                "kelly_fraction",
                "winner",
                "bankroll",
            ]
        },
        "merged_matches": {
            "order": [
                "match_id",
                "player_1",
                "player_2",
                "scheduled_time",
                "market_id",
                "selection_id",
                "final_ltp",
            ]
        },
    }

    @classmethod
    def patch_schema(cls, df, schema_name):
        if schema_name not in cls._schemas:
            raise ValueError(f"Schema not found: {schema_name}")
        cols = cls._schemas[schema_name]["order"]
        missing = [col for col in cols if col not in df.columns]
        for col in missing:
            df[col] = None
        return df[cols]
