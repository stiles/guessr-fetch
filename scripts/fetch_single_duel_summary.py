import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import config  # Load headers and cookies from config.py

# GeoGuessr Duel URL
duel_id = "89c51cdf-4484-4ea5-9bce-07e90003034a"
url = f"https://www.geoguessr.com/duels/{duel_id}/summary"

try:
    # Send GET request
    response = requests.get(url, headers=config.headers, cookies=config.cookies)
    response.raise_for_status()

    # Parse HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")

    if script_tag:
        # Extract and load the JSON content
        next_json = json.loads(script_tag.string)
        game_details = next_json['props']['pageProps']['game']

        # Extract result details
        result = game_details['result']
        winning_team_id = result.get('winningTeamId')
        is_draw = result.get('isDraw')

        # Extract rounds (actual locations)
        rounds = {r['roundNumber']: (r['panorama']['lat'], r['panorama']['lng']) for r in game_details['rounds']}

        # DataFrame rows
        data = []

        for team in game_details['teams']:
            for player in team['players']:
                if player['nick'] == 'stiles':  # Adjust nickname
                    team_id = team['id']  # Your team ID

                    # Determine win/loss/draw
                    if is_draw:
                        outcome = "Draw"
                    elif team_id == winning_team_id:
                        outcome = "Win"
                    else:
                        outcome = "Loss"

                    # Process guesses
                    for guess in player['guesses']:
                        round_number = guess['roundNumber']
                        guessed_lat, guessed_lng = guess['lat'], guess['lng']
                        distance = guess['distance']
                        score = guess['score']

                        # Actual location
                        actual_lat, actual_lng = rounds.get(round_number, (None, None))

                        # Append to data
                        data.append({
                            "id": duel_id,
                            "round_number": round_number,
                            "actual_lat": actual_lat,
                            "actual_lng": actual_lng,
                            "guess_lat": guessed_lat,
                            "guess_lng": guessed_lng,
                            "distance": distance,
                            "score": score,
                            "outcome": outcome  # Add win/loss/draw
                        })

        # Create DataFrame
        df = pd.DataFrame(data)
        print(df)

        # Optional: Save to CSV
        # df.to_csv(f"duel_{duel_id}_results.csv", index=False)

    else:
        print("Could not find the __NEXT_DATA__ script on the page.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching the page: {e}")
