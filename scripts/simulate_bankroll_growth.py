import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from tqdm import tqdm
import os


def load_value_bets(input_glob):
    files = glob(input_glob) if "*" in input_glob or "?" in input_glob else input_glob.split(",")
    if not files:
        raise FileNotFoundError(f"No files match: {input_glob}")
    return pd.concat([pd.read_csv(f).assign(source_file=os.path.basename(f)) for f in files], ignore_index=True)


def kelly_stake(prob, odds, bankroll, max_frac):
    edge = (odds - 1) * prob - (1 - prob)
    fraction = edge / (odds - 1) if odds > 1 else 0
    return bankroll * min(max(fraction, 0), max_frac)


def simulate(df, strategy, ev_thresh, odds_cap, max_frac, fixed_stake):
    bankroll = 1000.0
    peak = bankroll
    history = []

    df = df.drop_duplicates(subset=["player_1", "source_file"]).reset_index(drop=True)

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Simulating bankroll"):
        p1_ev = row.get("ev_p1_model", np.nan)
        p2_ev = row.get("ev_p2_model", np.nan)
        p_model = row.get("p_model", np.nan)
        p1_odds = row.get("odds_player_1", np.nan)
        p2_odds = row.get("odds_player_2", np.nan)
        winner = row.get("winner_name", "")

        bet_side = None
        if pd.notna(p1_ev) and p1_ev > ev_thresh and p1_odds <= odds_cap:
            prob = p_model
            odds = p1_odds
            stake = kelly_stake(prob, odds, bankroll, max_frac) if strategy == "kelly" else fixed_stake
            win = row["player_1"] == winner
            player = row["player_1"]
            ev = p1_ev
            bet_side = "p1"
        elif pd.notna(p2_ev) and p2_ev > ev_thresh and p2_odds <= odds_cap:
            prob = 1 - p_model
            odds = p2_odds
            stake = kelly_stake(prob, odds, bankroll, max_frac) if strategy == "kelly" else fixed_stake
            win = row["player_2"] == winner
            player = row["player_2"]
            ev = p2_ev
            bet_side = "p2"
        else:
            continue  # skip non-bets

        payout = stake * odds if win else 0
        profit = payout - stake
        bankroll += profit
        peak = max(peak, bankroll)

        history.append({
            "player_staked": player,
            "stake": stake,
            "player_payout": payout,
            "bankroll": bankroll,
            "profit": profit,
            "win": int(win),
            "ev": ev,
            "odds": odds,
            "strategy": strategy,
            "source_file": row["source_file"],
            "bet_side": bet_side
        })

    df_sim = pd.DataFrame(history)
    max_drawdown = peak - df_sim["bankroll"].min() if not df_sim.empty else 0.0
    return df_sim, max_drawdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_glob", required=False)
    parser.add_argument("--input_csvs", nargs="*")
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot_path")
    parser.add_argument("--ev_threshold", type=float, default=0.05)
    parser.add_argument("--odds_cap", type=float, default=10.0)
    parser.add_argument("--strategy", choices=["kelly", "fixed"], default="kelly")
    parser.add_argument("--fixed_stake", type=float, default=20.0)
    args = parser.parse_args()

    input_glob = ",".join(args.input_csvs) if args.input_csvs else args.input_glob
    df = load_value_bets(input_glob)

    required_cols = [
        "player_1", "player_2", "p_model", "ev_p1_model", "ev_p2_model",
        "odds_player_1", "odds_player_2", "winner_name", "source_file"
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    df_sim, max_dd = simulate(
        df,
        strategy=args.strategy,
        ev_thresh=args.ev_threshold,
        odds_cap=args.odds_cap,
        max_frac=0.02,
        fixed_stake=args.fixed_stake
    )

    df_sim.to_csv(args.output_csv, index=False)
    print(f"\n📈 Simulated {len(df_sim)} bets")
    print(f"💰 Final bankroll: {df_sim['bankroll'].iloc[-1]:.2f}")
    print(f"📉 Max drawdown: {max_dd:.2f}")

    if args.plot and not df_sim.empty:
        plt.figure(figsize=(10, 6))
        plt.plot(df_sim["bankroll"])
        plt.title(f"Bankroll Simulation ({args.strategy})")
        plt.xlabel("Bet #")
        plt.ylabel("Bankroll")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(args.plot_path)
        print(f"📈 Plot saved to {args.plot_path}")

if __name__ == "__main__":
    main()
