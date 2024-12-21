import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import pytz
from config import cookies, headers

# Date strings for storage
eastern = pytz.timezone("America/New_York")
today = datetime.now(eastern).strftime("%Y-%m-%d")

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
OUTPUT_PATH = BASE_DIR / "data" / "leaderboard" / "geoguessr_leaders_timeseries.json"

# Function to request the leaderboard and paginate to collect all the records
def fetch_all_pages(url, cookies, headers, limit=100, existing_ids=None):
    offset = 0
    all_records = []
    existing_ids = existing_ids or set()
    
    with tqdm(desc="Fetching records", unit="page") as pbar:
        while True:
            params = {'offset': str(offset), 'limit': str(limit)}
            response = requests.get(url, params=params, cookies=cookies, headers=headers)
            
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                break
            
            try:
                # Parse response
                records = response.json()
            except ValueError:
                print("Error: Failed to parse JSON response")
                break
            
            # Skip records that are already in the existing data
            new_records = [record for record in records if record.get('userId') not in existing_ids]
            
            if not new_records:
                print("No more new records to fetch.")
                break
            
            all_records.extend(new_records)
            existing_ids.update(record.get('userId') for record in new_records)
            offset += limit
            pbar.update(1)

    return all_records

# Load existing time series data if it exists
if OUTPUT_PATH.exists():
    try:
        old_df = pd.read_json(OUTPUT_PATH)
        existing_ids = set(old_df['id'])
    except ValueError:
        print(f"Warning: Failed to load existing data from {OUTPUT_PATH}. Starting fresh.")
        old_df = pd.DataFrame()
        existing_ids = set()
else:
    old_df = pd.DataFrame()
    existing_ids = set()

# Fetch the latest data
url = 'https://www.geoguessr.com/api/v4/ranked-system/ratings'
new_data = fetch_all_pages(url, cookies, headers, existing_ids=existing_ids)

# Create DataFrame for the latest data
if new_data:
    new_df = pd.DataFrame(new_data).drop(['isDeleted', 'flair'], axis=1, errors='ignore').rename(columns={'countryCode': 'country', 'isVerified':'verified', 'userId':'id'})
    new_df['date'] = today
else:
    print("No new data fetched. Exiting.")
    exit()

# Concatenate old and new data
combined_df = pd.concat([old_df, new_df], ignore_index=True)

# Drop unwanted columns if they exist
columns_to_drop = ['avatar', 'fullBodyPath']
combined_df = combined_df.drop(columns=[col for col in columns_to_drop if col in combined_df.columns], errors='ignore')

# Remove duplicates based on 'id' and 'date'
combined_df.drop_duplicates(subset=['id', 'date'], inplace=True)

# Save updated time series data
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
combined_df.to_json(OUTPUT_PATH, indent=4, orient='records')

print(f"Data successfully updated and saved to {OUTPUT_PATH}")
