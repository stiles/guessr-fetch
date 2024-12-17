import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import pytz
from config import cookies, headers

# Date strings for storage
today = pd.Timestamp("today").strftime("%Y-%m-%d")
eastern = pytz.timezone("America/New_York")
now = datetime.now(eastern)

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
INPUT_PATH = BASE_DIR / "static" / "data" / "leaderboard" / "leaders.json"
OUTPUT_PATH = BASE_DIR / "static" / "data" / "leaderboard" / "geoguessr_leaders_timeseries.json"

# Function to request the leaderboard and paginate to collect all the records
def fetch_all_pages(url, cookies, headers, limit=100):
    offset = 0
    all_records = []
    
    with tqdm(desc="Fetching records", unit="page") as pbar:
        while True:
            params = {'offset': str(offset), 'limit': str(limit)}
            response = requests.get(url, params=params, cookies=cookies, headers=headers)
            
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                break
            
            # Parse response
            records = response.json()
            
            if not records:
                print("No more records to fetch.")
                break
            
            all_records.extend(records)
            offset += limit
            pbar.update(1)

    return all_records

# Fetch the latest data 
url = 'https://www.geoguessr.com/api/v4/ranked-system/ratings'
new_data = fetch_all_pages(url, cookies, headers)

# Create DataFrame for the latest data
new_df = pd.DataFrame(new_data)
new_df['fetched_date'] = today

# Load existing time series data if it exists
if OUTPUT_PATH.exists():
    old_df = pd.read_json(OUTPUT_PATH)
else:
    old_df = pd.DataFrame()

# Concatenate old and new data, then drop duplicates based on keys
combined_df = pd.concat([old_df, new_df], ignore_index=True).drop(['avatar', 'fullBodyPath'], axis=1)
combined_df.drop_duplicates(subset=['userId', 'fetched_date'], inplace=True)

# Save updated time series data
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
combined_df.to_json(OUTPUT_PATH, indent=4, orient='records')

print(f"Data successfully updated and saved to {OUTPUT_PATH}")