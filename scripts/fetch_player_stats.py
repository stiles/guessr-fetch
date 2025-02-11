import requests
import os
import sys
import json
from tqdm import tqdm
from config import cookies, headers
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

# Paths
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(BASE_DIR)

ARCHIVE_INPUT = f"./data/leaderboard/geoguessr_leaders_timeseries.json"
RAW_DATA_DIR = f"./data/leaderboard/raw_player_data"
LOG_FILE = f"./data/leaderboard/processed_users.log"

# Ensure the raw data directory and log file exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "w").close()

# Read the leaderboard data
timeseries_df = pd.read_json(ARCHIVE_INPUT)

# As of the most recent leaderboard fetch
latest_df = timeseries_df.query("fetched == fetched.max()").sort_values('rating', ascending=False).reset_index(drop=True)

# List of player IDs
ranked_users_list = latest_df.id.to_list()

# Read the log file to get already processed users
with open(LOG_FILE, "r") as log:
    processed_users = set(line.strip() for line in log)

# Filter out already processed users
remaining_users = [user_id for user_id in ranked_users_list if user_id not in processed_users]

# Process users in batches of 1,000
batch_size = 1000
for i in range(0, len(remaining_users), batch_size):
    batch = remaining_users[i : i + batch_size]
    print(f"Processing batch {i // batch_size + 1} with {len(batch)} users...")

    for user_id in tqdm(batch):
        try:
            raw_file_path = os.path.join(RAW_DATA_DIR, f"{user_id}.json")
            # Skip if the raw data already exists
            if os.path.exists(raw_file_path):
                continue

            url = f"https://www.geoguessr.com/user/{user_id}"
            response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
            response.raise_for_status()

            # Extract raw __NEXT_DATA__
            player_html = BeautifulSoup(response.text, "html.parser")
            json_str = player_html.find("script", id="__NEXT_DATA__")
            if not json_str:
                print(f"No __NEXT_DATA__ for user {user_id}, skipping.")
                continue

            # Save raw JSON to file
            with open(raw_file_path, "w") as f:
                f.write(json_str.text)

            # Log the processed user
            with open(LOG_FILE, "a") as log:
                log.write(f"{user_id}\n")

            # Random sleep to avoid detection
            time.sleep(random.randint(1, 3))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for user {user_id}: {e}")
            continue

print("All batches processed!")
