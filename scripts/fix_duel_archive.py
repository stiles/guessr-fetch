import os
import json
import pandas as pd
from datetime import datetime

# Define the path to the individual JSON files and output file
INDIVIDUAL_DUMP_PATH = "./data/duels/all/individual_dump"
OUTPUT_FILE = "./data/duels/all/stiles_duel_results.json"

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

# Initialize list to collect data
all_data = []

# Function to process individual duel files
def process_duel_file(filepath):
    try:
        with open(filepath, "r") as file:
            duel_data = json.load(file)

        # Extract game ID
        game_id = duel_data.get("gameId", os.path.splitext(os.path.basename(filepath))[0])

        # Extract rounds data
        rounds_data = {round_["roundNumber"]: round_["panorama"] for round_ in duel_data["rounds"]}

        # Extract relevant data from teams
        for team in duel_data.get("teams", []):
            for player in team.get("players", []):
                if player.get("nick") == "stiles":  # Adjust to your username
                    # Determine duel outcome
                    outcome = "Draw"
                    if duel_data.get("result", {}).get("winningTeamId") == team.get("id"):
                        outcome = "Win"
                    elif duel_data.get("result", {}).get("winningTeamId") is not None:
                        outcome = "Loss"

                    # Opponent nickname
                    opponent_nick = next(
                        (p["nick"] for t in duel_data["teams"] for p in t["players"] if p["nick"] != "stiles"),
                        None,
                    )

                    # Process guesses
                    for guess in player.get("guesses", []):
                        round_number = guess["roundNumber"]
                        actual = rounds_data.get(round_number, {})

                        # Normalize data
                        row = unified_schema.copy()
                        row.update({
                            "duel_id": game_id,
                            "created": datetime.utcfromtimestamp(guess.get("created", 0) / 1000).isoformat() + "Z"
                            if guess.get("created")
                            else None,
                            "duel_outcome": outcome,
                            "duel_opponent": opponent_nick,
                            "duel_round_num": round_number,
                            "actual_lat": actual.get("lat"),
                            "actual_lng": actual.get("lng"),
                            "my_guess_lat": guess.get("lat"),
                            "my_guess_lng": guess.get("lng"),
                            "my_guess_distance": guess.get("distance"),
                            "my_guess_miles": round(guess.get("distance", 0) / 1609, 4) if guess.get("distance") else None,
                            "my_health_after": guess.get("score"),
                        })
                        all_data.append(row)

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

# Process all files
for file in os.listdir(INDIVIDUAL_DUMP_PATH):
    if file.endswith(".json"):
        process_duel_file(os.path.join(INDIVIDUAL_DUMP_PATH, file))

# Save to output file
if all_data:
    df = pd.DataFrame(all_data)
    df.to_json(OUTPUT_FILE, orient="records", indent=4)
    print(f"Rebuilt data saved to {OUTPUT_FILE}")
else:
    print("No data found to reconstruct.")
