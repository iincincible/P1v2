# scripts/list_tennis_events.py

import os
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport_key", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise ValueError("Missing ODDS_API_KEY environment variable")

    start = datetime.fromisoformat(args.start_date)
    end = datetime.fromisoformat(args.end_date)

    all_events = []
    for day in (start + timedelta(n) for n in range((end - start).days + 1)):
        iso_day = day.strftime("%Y-%m-%dT00:00:00Z")
        url = f"https://api.the-odds-api.com/v4/historical/sports/{args.sport_key}/events"
        params = {"apiKey": api_key, "date": iso_day}
        r = requests.get(url, params=params)
        if r.status_code != 200:
            print(f"❌ {iso_day} - status {r.status_code}")
            continue

        try:
            events = r.json()
            if not isinstance(events, list):
                print(f"⚠️  Unexpected response on {iso_day}: {events}")
                continue
        except Exception as e:
            print(f"❌ Failed to parse JSON on {iso_day}: {e}")
            continue

        print(f"📅 {iso_day} - {len(events)} events")
        for e in events:
            all_events.append({
                "event_id": e.get("id", ""),
                "commence_time": e.get("commence_time", ""),
                "home_team": e.get("home_team", ""),
                "away_team": e.get("away_team", ""),
                "bookmakers": len(e.get("bookmakers", [])) if "bookmakers" in e else 0
            })

    df = pd.DataFrame(all_events)
    df.to_csv(args.output_csv, index=False)
    print(f"✅ Saved {len(df)} events to {args.output_csv}")

if __name__ == "__main__":
    main()
