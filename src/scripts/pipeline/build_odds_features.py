import argparse
import pandas as pd
from pathlib import Path
from scripts.utils.logger import log_info, log_success, log_warning, log_error
from scripts.utils.cli_utils import add_common_flags

def main(args=None):
    parser = argparse.ArgumentParser(description="Build odds features for match predictions.")
    parser.add_argument("--input_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    add_common_flags(parser)
    _args = parser.parse_args(args)

    input_path = Path(_args.input_csv)
    output_path = Path(_args.output_csv)

    try:
        df = pd.read_csv(input_path)
        log_info(f"Loaded {len(df)} rows from {input_path}")

        # =============== BEGIN YOUR CUSTOM FEATURE LOGIC ===============
        # This is where your existing feature engineering would go
        # e.g., df["implied_prob_1"] = 1 / df["odds_player_1"]

        # =============== PATCH: Always create 'odds' column ===============
        if 'odds' not in df.columns:
            if 'odds_player_1' in df.columns:
                df['odds'] = df['odds_player_1']
                log_info("🔧 Created 'odds' column from 'odds_player_1'")
            elif 'odds_player_2' in df.columns:
                df['odds'] = df['odds_player_2']
                log_info("🔧 Created 'odds' column from 'odds_player_2'")
            else:
                log_warning("No odds source found! 'odds' column missing in features.")
        # =============== END PATCH ===============

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"✅ Saved odds features to {output_path}")

    except Exception as e:
        log_error(f"❌ Failed to build/save odds features: {e}")

if __name__ == "__main__":
    main()
