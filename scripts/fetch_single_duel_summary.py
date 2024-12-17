import os
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import config  # Load user-specific headers and cookies from config.py

username = 'stiles'

# Function to process a single duel and extract data
def process_single_duel(duel_id, save_path):
    url = f"https://www.geoguessr.com/duels/{duel_id}/summary"
    all_data = []

    try:
        # Send GET request
        response = requests.get(url, headers=config.headers, cookies=config.cookies)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if script_tag:
            # Extract JSON and game details
            game_data = json.loads(script_tag.string)
            duel_details = game_data['props']['pageProps']['game']

            # Extract result details
            result = duel_details['result']
            winning_team_id = result.get('winningTeamId')
            is_draw = result.get('isDraw')

            # Extract rounds (actual locations)
            rounds = {r['roundNumber']: (r['panorama']['lat'], r['panorama']['lng']) for r in duel_details['rounds']}

            # Identify opponent's nickname
            opponent_nick = None
            for team in duel_details['teams']:
                for player in team['players']:
                    if player['nick'] != f'{username}':  # Opponent check
                        opponent_nick = player['nick']
                        break

            # Process guesses
            for team in duel_details['teams']:
                for player in team['players']:
                    if player['nick'] == f'{username}':  # Adjust nickname
                        team_id = team['id']  # Your team ID

                        # Determine outcome
                        if is_draw:
                            outcome = "Draw"
                        elif team_id == winning_team_id:
                            outcome = "Win"
                        else:
                            outcome = "Loss"

                        for guess in player['guesses']:
                            round_number = guess['roundNumber']
                            guessed_lat, guessed_lng = guess['lat'], guess['lng']
                            distance = guess['distance']
                            score = guess['score']

                            # Actual location
                            actual_lat, actual_lng = rounds.get(round_number, (None, None))

                            all_data.append({
                                "duel_id": duel_id,
                                "duel_outcome": outcome,
                                "duel_opponent": opponent_nick,
                                "duel_round_num": round_number,
                                "actual_lat": actual_lat,
                                "actual_lng": actual_lng,
                                "my_guess_lat": guessed_lat,
                                "my_guess_lng": guessed_lng,
                                "my_guess_distance": distance,
                                "my_guess_miles": round(distance / 1609, 4),
                                "my_health_after": score,
                            })

            # Save to JSON
            results_path = os.path.join(save_path, f"{duel_id}.json")
            with open(results_path, "w") as file:
                json.dump(all_data, file, indent=4)
            print(f"Saved duel {duel_id} results to {results_path}")

            # Convert to DataFrame and print
            df = pd.DataFrame(all_data)
            print(df)

        else:
            print(f"No __NEXT_DATA__ found for duel {duel_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching duel {duel_id}: {e}")


# Main script logic
if __name__ == "__main__":
    duel_id = "89c51cdf-4484-4ea5-9bce-07e90003034a"  # Replace with your duel ID
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    save_path = os.path.join(script_dir, "..", "data", "duels", 'individual')
    os.makedirs(save_path, exist_ok=True)

    process_single_duel(duel_id, save_path)