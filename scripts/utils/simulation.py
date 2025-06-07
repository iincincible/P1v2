import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

from scripts.utils.betting_math import compute_kelly_stake_capped

def simulate_bankroll(
    df: pd.DataFrame,
    strategy: str = "kelly",
    initial_bankroll: float = 1000.0,
    ev_threshold: float = 0.01,
    odds_cap: float = 100.0,
    cap_fraction: float = 0.05,
    verbose: bool = True
) -> tuple[pd.DataFrame, float, float]:
    """
    Simulates betting bankroll over time using either flat or Kelly staking.
    Returns:
        - DataFrame with log per bet
        - Final bankroll
        - Max drawdown
    """
    bankroll = initial_bankroll
    peak = bankroll
    max_drawdown = 0.0
    history = []

    filtered = df.copy()
    filtered = filtered.dropna(subset=["predicted_prob", "odds", "expected_value", "winner"])
    filtered = filtered[
        (filtered["expected_value"] >= ev_threshold) &
        (filtered["odds"] <= odds_cap)
    ]

    if verbose:
        print(f"📊 Starting bankroll: {initial_bankroll:.2f}")
        print(f"✅ {len(filtered)} bets after EV and odds filters")

    # Fallback to flat if too few bets
    actual_strategy = strategy
    if strategy == "kelly" and len(filtered) < 10:
        print(f"⚠️ Only {len(filtered)} bets — switching to flat staking for safety.")
        actual_strategy = "flat"

    for _, row in tqdm(filtered.iterrows(), total=len(filtered), desc="Simulating bankroll"):
        prob = row["predicted_prob"]
        odds = row["odds"]
        won = row["winner"]

        stake = 1.0 if actual_strategy == "flat" else compute_kelly_stake_capped(prob, odds, bankroll, cap=cap_fraction)
        payout = stake * (odds if won else 0)
        bankroll += payout - stake
        peak = max(peak, bankroll)
        drawdown = peak - bankroll
        max_drawdown = max(max_drawdown, drawdown)

        history.append({
            "match_id": row.get("match_id", ""),
            "stake": stake,
            "odds": odds,
            "won": bool(won),
            "payout": payout,
            "bankroll": bankroll
        })

    return pd.DataFrame(history), bankroll, max_drawdown

def generate_bankroll_plot(bankroll_series: pd.Series, output_path: str = None):
    """
    Generates and saves a bankroll trajectory plot.
    """
    if bankroll_series.empty:
        print("⚠️ No bankroll data to plot.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(bankroll_series, color="blue")
    plt.xlabel("Bet Number")
    plt.ylabel("Bankroll")
    plt.title("Bankroll Over Time")
    plt.grid(True)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path)
        print(f"🖼️ Saved plot to {output_path}")
    else:
        plt.show()
