import json
import csv
import argparse

def convert_json_to_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for match in data['data']:
        if len(match['bookmakers']) == 0:
            continue
        bookmaker = match['bookmakers'][0]
        if len(bookmaker['markets']) == 0:
            continue
        market = bookmaker['markets'][0]
        outcomes = market.get('outcomes', [])
        if len(outcomes) != 2:
            continue

        player1 = outcomes[0]['name'].strip()
        player2 = outcomes[1]['name'].strip()
        odds_p1 = outcomes[0]['price']
        odds_p2 = outcomes[1]['price']
        start_time = match['commence_time']

        rows.append({
            'commence_time': start_time,
            'player1': player1,
            'player2': player2,
            'odds_p1': odds_p1,
            'odds_p2': odds_p2
        })

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['commence_time', 'player1', 'player2', 'odds_p1', 'odds_p2'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Converted {len(rows)} matches to CSV: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_json', required=True)
    parser.add_argument('--output_csv', required=True)
    args = parser.parse_args()

    convert_json_to_csv(args.input_json, args.output_csv)
