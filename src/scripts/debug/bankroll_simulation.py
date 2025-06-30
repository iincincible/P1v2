import matplotlib.pyplot as plt
import pandas as pd

CSV_PATH = "data/processed/ausopen_2023_atp_value_bets.csv"
STARTING_BANKROLL = 1000
FRACTIONAL_KELLY = 0.01  # Use 1% Kelly for sanity
MAX_KELLY = 0.02  # Never bet more than 2% Kelly

df = pd.read_csv(CSV_PATH)

# Print extreme Kelly stakes and predicted probabilities
print("Top 10 Kelly stakes:")
print(
    df.sort_values("kelly_stake", ascending=False).head(10)[
        ["player_1", "player_2", "odds", "predicted_prob", "kelly_stake"]
    ]
)
print("\nTop 10 predicted probabilities:")
print(
    df.sort_values("predicted_prob", ascending=False).head(10)[
        ["player_1", "player_2", "odds", "predicted_prob", "kelly_stake"]
    ]
)

# Sanity-check Kelly formula
df["sanity_kelly"] = (
    df["predicted_prob"] * (df["odds"] - 1) - (1 - df["predicted_prob"])
) / (df["odds"] - 1)
print("\nSanity check on Kelly calculation:")
print(df[["kelly_stake", "sanity_kelly"]].head(10))

# Conservative Fractional Kelly simulation
bankroll_kelly = STARTING_BANKROLL
history_kelly = []

for idx, row in df.iterrows():
    kelly = row["kelly_stake"] * FRACTIONAL_KELLY
    kelly = max(kelly, 0)
    kelly = min(kelly, MAX_KELLY)
    bet = bankroll_kelly * kelly
    bet = min(bet, bankroll_kelly)
    if bet < 1e-8:
        history_kelly.append(bankroll_kelly)
        continue
    win = row["winner"] == 1
    payout = bet * (row["odds"] - 1) if win else -bet
    bankroll_kelly += payout
    history_kelly.append(bankroll_kelly)

plt.figure(figsize=(10, 6))
plt.plot(
    history_kelly,
    label=f"Fractional Kelly ({FRACTIONAL_KELLY*100:.0f}% Kelly, Max {MAX_KELLY*100:.0f}%)",
)
plt.xlabel("Bet #")
plt.ylabel("Bankroll")
plt.title("Bankroll Evolution (Conservative Kelly)")
plt.legend()
plt.tight_layout()
plt.show()

print(f"\nFinal bankroll (Conservative Kelly): {bankroll_kelly:.2f}")
print(f"Max bankroll: {max(history_kelly):.2f}")
print(f"Min bankroll: {min(history_kelly):.2f}")
