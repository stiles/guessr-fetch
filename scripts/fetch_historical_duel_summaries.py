import sqlite3
import os
import shutil
import tempfile
import re
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import config
from datetime import datetime

username = 'stiles'

# Unified schema for consistency
unified_schema = {
    "duel_id": None,
    "created": None,
    "duel_outcome": None,
    "duel_opponent": None,
    "duel_round_num": None,
    "actual_lat": None,
    "actual_lng": None,
    "my_guess_lat": None,
    "my_guess_lng": None,
    "my_guess_distance": None,
    "my_guess_miles": None,
    "my_health_after": None,
}


# Access your Chrome history and extract duel IDs
def get_duel_ids():
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


# Fetch duel summary, save JSON, and parse data
def process_duel(duel_id, save_path, all_data, existing_ids):
    if duel_id in existing_ids:
        print(f"Skipping already processed duel {duel_id}")
        return

    url = f"https://www.geoguessr.com/duels/{duel_id}/summary"
    try:
        response = requests.get(url, headers=config.headers, cookies=config.cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if script_tag:
            game_data = json.loads(script_tag.string)
            duel_details = game_data['props']['pageProps']['game']

            start_time_ms = duel_details['rounds'][0].get('startTime')
            created_datetime = (
                datetime.utcfromtimestamp(start_time_ms / 1000).isoformat() + "Z"
                if start_time_ms else None
            )

            with open(os.path.join(save_path, f"{duel_id}.json"), "w") as file:
                json.dump(duel_details, file, indent=4)

            result = duel_details['result']
            winning_team_id = result.get('winningTeamId')
            is_draw = result.get('isDraw')

            rounds = {r['roundNumber']: (r['panorama']['lat'], r['panorama']['lng']) for r in duel_details['rounds']}
            opponent_nick = next(
                (p["nick"] for t in duel_details["teams"] for p in t["players"] if p["nick"] != username),
                None,
            )

            for team in duel_details['teams']:
                for player in team['players']:
                    if player['nick'] == username:
                        team_id = team['id']

                        outcome = "Draw"
                        if is_draw:
                            outcome = "Draw"
                        elif team_id == winning_team_id:
                            outcome = "Win"
                        else:
                            outcome = "Loss"

                        for guess in player.get("guesses", []):
                            round_number = guess["roundNumber"]
                            guessed_lat, guessed_lng = guess["lat"], guess["lng"]
                            distance = guess["distance"]
                            score = guess["score"]

                            actual_lat, actual_lng = rounds.get(round_number, (None, None))

                            # Normalize and append data
                            row = unified_schema.copy()
                            row.update({
                                "duel_id": duel_id,
                                "created": created_datetime,
                                "duel_outcome": outcome,
                                "duel_opponent": opponent_nick,
                                "duel_round_num": round_number,
                                "actual_lat": actual_lat,
                                "actual_lng": actual_lng,
                                "my_guess_lat": guessed_lat,
                                "my_guess_lng": guessed_lng,
                                "my_guess_distance": distance,
                                "my_guess_miles": round(distance / 1609, 4) if distance else None,
                                "my_health_after": score,
                            })
                            all_data.append(row)

            print(f"Processed duel {duel_id}")

        else:
            print(f"No __NEXT_DATA__ found for duel {duel_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching duel {duel_id}: {e}")


# Combine everything
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, "..")
    save_path = os.path.join(root_dir, "data", "duels", "all", "individual_dump")
    os.makedirs(save_path, exist_ok=True)

    results_json = os.path.join(root_dir, "data", "duels", "all", f"{username}_duel_results.json")

    all_data = []
    if os.path.exists(results_json):
        try:
            loaded_data = pd.read_json(results_json).to_dict(orient="records")
            for entry in loaded_data:
                row = unified_schema.copy()
                row.update(entry)
                all_data.append(row)
            print(f"Loaded {len(all_data)} existing duel results.")
        except ValueError:
            print("Error: Unable to read existing JSON data. Starting fresh.")

    existing_ids = {file.split(".")[0] for file in os.listdir(save_path) if file.endswith(".json")}
    processed_ids = {entry["duel_id"] for entry in all_data}

    print("Extracting duel IDs from Chrome history...")
    duel_ids = get_duel_ids()
    print(f"Found {len(duel_ids)} unique duels!")

    for duel_id in duel_ids:
        if duel_id not in processed_ids:
            process_duel(duel_id, save_path, all_data, existing_ids)

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_json(results_json, indent=4, orient="records")
        print(f"Saved all duel results to {results_json}")
    else:
        print("No duel data found.")

    print("All duels processed and saved.")


if __name__ == "__main__":
    main()
