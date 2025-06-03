import os
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from time import sleep
from tqdm import tqdm

# Read API key
API_KEY = os.getenv("ODDS_API_KEY")
if not API_KEY:
    raise ValueError("Missing ODDS_API_KEY environment variable.")

def fetch_snapshot(sport_key, iso_date):
    url = f"https://api.the-odds-api.com/v4/historical/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us,uk,eu,au",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "date": iso_date
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"⚠️ {iso_date} - Error {response.status_code}: {response.text}")
        return []

    try:
        return response.json()
    except Exception as e:
        print(f"❌ JSON decode error on {iso_date}: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport_key", required=True, help="e.g. tennis_atp_aus_open_singles")
    parser.add_argument("--output_path", required=True, help="Output CSV path")
    parser.add_argument("--start_date", default="2023-01-16", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", default="2023-01-30", help="End date (YYYY-MM-DD)")
    parser.add_argument("--snapshot_hour", type=int, default=2, help="Hour of day to fetch (default: 2AM UTC)")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")
    snapshot_hour = args.snapshot_hour

    results = []

    print(f"\n🎾 Fetching odds for {args.sport_key} from {args.start_date} to {args.end_date}")

    for i in tqdm(range((end - start).days + 1), desc="Fetching Odds Snapshots"):
        date = start + timedelta(days=i)
        snapshot_time = date.replace(hour=snapshot_hour)
        iso_date = snapshot_time.isoformat() + "Z"

        data = fetch_snapshot(args.sport_key, iso_date)

        if isinstance(data, dict) and "data" in data:
            events = data["data"]
        elif isinstance(data, list):
            events = data
        else:
            print(f"⚠️ {iso_date} - Unexpected response format")
            continue

        if not events:
            print(f"⚠️ {iso_date} - No events found")
            continue

        for event in events:
            teams = event.get("teams", [])
            print(f"\n🎾 Event: {teams} — Start: {event.get('commence_time')}")

            for bookmaker in event.get("bookmakers", []):
                print(f"  📚 Bookmaker: {bookmaker['title']} ({bookmaker['key']})")

                for market in bookmaker.get("markets", []):
                    if market.get("key") != "h2h":
                        continue

                    outcomes = market.get("outcomes", [])
                    if len(outcomes) != 2:
                        continue

                    try:
                        p1, p2 = outcomes[0]["name"], outcomes[1]["name"]
                        o1, o2 = outcomes[0]["price"], outcomes[1]["price"]
                        results.append({
                            "snapshot_date": iso_date,
                            "player_1": p1,
                            "player_2": p2,
                            "odds_player_1": o1,
                            "odds_player_2": o2,
                            "implied_prob_1": 1 / o1,
                            "implied_prob_2": 1 / o2,
                            "bookmaker": bookmaker["title"],
                        })
                        print(f"    ✅ {p1} vs {p2} — {o1}, {o2}")
                    except Exception as e:
                        print(f"    ❌ Error parsing outcome: {str(e)}")

        sleep(1.5)

    # Save
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    df.to_csv(args.output_path, index=False)
    print(f"\n✅ Saved {len(df)} odds rows to {args.output_path}")

if __name__ == "__main__":
    main()
