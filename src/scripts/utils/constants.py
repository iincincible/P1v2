# Default thresholds used across modeling and betting scripts
DEFAULT_EV_THRESHOLD = 0.2         # Minimum expected value for filtering
DEFAULT_MAX_ODDS = 6.0             # Odds cap for value bet filtering
DEFAULT_MAX_MARGIN = 0.05          # Max bookmaker margin allowed

# Simulation / bankroll behavior
DEFAULT_STRATEGY = "kelly"         # Default staking strategy
DEFAULT_FIXED_STAKE = 10.0         # Flat stake per bet (if strategy = flat)
DEFAULT_INITIAL_BANKROLL = 1000.0  # Starting bankroll value
KELLY_CAP_FRACTION = 0.05          # Max % bankroll allowed on any Kelly stake

# Modeling
DEFAULT_MODEL_PATH = "modeling/win_model.pkl"  # Fallback path for prediction model

# Configuration
DEFAULT_CONFIG_FILE = "configs/tournaments_2024.yaml"
