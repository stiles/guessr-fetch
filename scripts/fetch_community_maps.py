import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import pytz
from config import cookies, headers
import string

# Date strings for storage
eastern = pytz.timezone("America/New_York")
today = datetime.now(eastern).strftime("%Y-%m-%d")

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
OUTPUT_PATH = BASE_DIR / "data" / "maps" / f"geoguessr_all_world_maps_{today}.json"

def fetch_geoguessr_maps():
    """
    Fetch all world maps from the GeoGuessr API and return as a DataFrame.
    """
    maps_data = []
    letters = list(string.ascii_lowercase)
    
    for letter in tqdm(letters, desc="Querying letters"):
        page = 0
        while True:
            params = {
                'query': letter,
                'page': str(page),
                'count': '50',
            }
            
            response = requests.get(
                'https://www.geoguessr.com/api/v3/search/any',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            
            if response.status_code != 200:
                print(f"Error fetching letter '{letter}', page {page}: {response.status_code}")
                break
            
            data = response.json()
            if not data:  # Exit if no more records are returned
                print(f"No more results for letter '{letter}' on page {page}")
                break
            
            # Flatten and store relevant data
            for record in data:
                maps_data.append({
                    'id': record.get('id'),
                    'name': record.get('name'),
                    'description': record.get('description'),
                    'likes': record.get('likes'),
                    'coordinateCount': record.get('coordinateCount'),
                    'numberOfGamesPlayed': record.get('numberOfGamesPlayed'),
                    'isUserMap': record.get('isUserMap'),
                    'creatorId': record.get('creatorId'),
                    'created': record.get('created'),
                    'updated': record.get('updated'),
                    'imageUrl': record.get('imageUrl'),
                    'creator': record.get('creator'),
                    'type': record.get('type'),
                })
            
            print(f"Appended {len(data)} records for letter '{letter}', page {page}")
            page += 1
    
    # Convert to DataFrame and remove duplicates
    maps_df = pd.DataFrame(maps_data)
    print(f"Total records before deduplication: {len(maps_df)}")
    maps_df = maps_df.drop_duplicates(subset='id')
    print(f"Total records after deduplication: {len(maps_df)}")

    maps_df = maps_df.query("~creator.isnull()").sort_values(
            "numberOfGamesPlayed", ascending=False
        )
    
    return maps_df

# Fetch and save maps
if __name__ == "__main__":
    all_maps_df = fetch_geoguessr_maps()
    
    # Save to JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    all_maps_df.to_json(OUTPUT_PATH, orient="records", indent=4)
    print(f"Saved {len(all_maps_df)} records to {OUTPUT_PATH}")