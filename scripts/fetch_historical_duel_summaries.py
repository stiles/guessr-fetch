import sqlite3
import os
import shutil
import tempfile
import re
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import config  # Load session headers and cookies in a config.py file for auth

# Step 1: Access your Chrome history and extract duel IDs
def get_duel_ids():
    # Path to Chrome history file for mac user
    chrome_history = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
    temp_history = os.path.join(tempfile.gettempdir(), "History_copy")

    # Copy history database to avoid locking issues
    shutil.copy2(chrome_history, temp_history)

    connection = sqlite3.connect(temp_history)
    cursor = connection.cursor()

    # Query to get URLs
    query = "SELECT url FROM urls"
    cursor.execute(query)

    # Extract duel IDs
    duels = []
    for url, in cursor.fetchall():
        if url.startswith("https://www.geoguessr.com") and not url.endswith(("summary", "replay")):
            duel_match = re.search(r"/duels/([^/?]+)", url)
            if duel_match:
                duels.append(duel_match.group(1))

    connection.close()
    os.remove(temp_history)
    return list(set(duels))  # Remove duplicates


# Step 2: Fetch duel summary, save JSON, and parse data
def process_duel(duel_id, save_path, all_data):
    url = f"https://www.geoguessr.com/duels/{duel_id}/summary"
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

            # Save the JSON to a file
            with open(os.path.join(save_path, f"{duel_id}.json"), "w") as file:
                json.dump(duel_details, file, indent=4)

            # Extract result details
            result = duel_details['result']
            winning_team_id = result.get('winningTeamId')
            is_draw = result.get('isDraw')

            # Extract rounds (actual locations)
            rounds = {r['roundNumber']: (r['panorama']['lat'], r['panorama']['lng']) for r in duel_details['rounds']}

            # Identify the opponent's nickname
            opponent_nick = None
            for team in duel_details['teams']:
                for player in team['players']:
                    if player['nick'] != 'stiles':  # Opponent check
                        opponent_nick = player['nick']
                        break

            # Process guesses
            for team in duel_details['teams']:
                for player in team['players']:
                    if player['nick'] == 'stiles':  # Adjust nickname
                        team_id = team['id']  # Your team ID

                        # Determine outcome
                        if is_draw:
                            outcome = "Draw"
                        elif team_id == winning_team_id:
                            outcome = "Win"
                        else:
                            outcome = "Loss"

                        # Append each guess to all_data
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

            print(f"Processed duel {duel_id}")

        else:
            print(f"No __NEXT_DATA__ found for duel {duel_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching duel {duel_id}: {e}")



# Step 3: Combine everything
def main():
    # Ensure consistent paths regardless of execution location
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    root_dir = os.path.join(script_dir, "..")  # Go one level up to root
    save_path = os.path.join(root_dir, "static", "data", "duels")  # Target directory
    os.makedirs(save_path, exist_ok=True)

    # Initialize list to collect all data
    all_data = []

    # Step 1: Get duel IDs from history
    print("Extracting duel IDs from Chrome history...")
    duel_ids = get_duel_ids()
    print(f"Found {len(duel_ids)} unique duels!")

    # Step 2: Process each duel
    for duel_id in duel_ids:
        process_duel(duel_id, save_path, all_data)

    # Step 3: Save all data to a DataFrame
    if all_data:
        results_json = os.path.join(root_dir, "static", "data", "duel_results.json")
        df = pd.DataFrame(all_data)
        df.to_json(results_json, indent=4, orient='records')
        print(f"Saved all duel results to {results_json}")
    else:
        print("No duel data found.")

    print("All duels processed and saved.")

if __name__ == "__main__":
    main()