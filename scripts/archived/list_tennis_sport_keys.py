import requests
import os

API_KEY = os.getenv("ODDS_API_KEY")
if not API_KEY:
    raise ValueError("Missing ODDS_API_KEY environment variable.")

url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}&all=true"
response = requests.get(url)

if response.status_code != 200:
    print(f"❌ API Error {response.status_code}: {response.text}")
    exit()

sports = response.json()
print("🎾 Available tennis sport keys:\n")

for sport in sports:
    if "tennis" in sport["key"]:
        print(f"{sport['key']:35} — {sport['title']}")
