# scripts/check_indianwells_events.py
import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")
sport_key = "tennis_atp_indian_wells"
date = "2023-03-10T12:00:00Z"

url = f"https://api.the-odds-api.com/v4/historical/sports/{sport_key}/events"
params = {"apiKey": API_KEY, "date": date}

r = requests.get(url, params=params)
print(f"Status {r.status_code}")
print(r.json())
