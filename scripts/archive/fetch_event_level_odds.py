# scripts/fetch_event_level_odds.py

import os
import argparse
import requests
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport_key", required=True)
    parser.add_argument("--event_id", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise ValueError("Missing ODDS_API_KEY environment variable")

    url = f"https://api.the-odds-api.com/v4/historical/sports/{args.sport_key}/events/{args.event_id}/odds"
    params = {
        "apiKey": api_key,
        "date": args.date,
        "markets": "h2h",
        "regions": "au",
        "oddsFormat": "decimal"
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        raise Exception(f"❌ Status {r.status_code}: {r.text}")

    data = r.json()
    rows = []
    for bookmaker in data.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                rows.append({
                    "event_id": args.event_id,
                    "snapshot": args.date,
                    "bookmaker": bookmaker["title"],
                    "last_update": bookmaker["last_update"],
                    "player": outcome["name"],
                    "price": outcome["price"]
                })

    df = pd.DataFrame(rows)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved odds for event {args.event_id} to {args.output_csv}")

if __name__ == "__main__":
    main()
