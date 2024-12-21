import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import rcParams

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
OUTPUT_PATH = BASE_DIR / "data" / "leaderboard" / "geoguessr_leaders_timeseries.json"
VISUALS_PATH = BASE_DIR / "visuals" / "charts"

rcParams['font.family'] = 'Roboto'

# Ensure the visuals directory exists
VISUALS_PATH.mkdir(parents=True, exist_ok=True)

# Load the leaderboard data
if not OUTPUT_PATH.exists():
    print(f"Error: Leaderboard data file not found at {OUTPUT_PATH}")
    exit()

try:
    leaderboard_df = pd.read_json(OUTPUT_PATH)
except ValueError:
    print(f"Error: Failed to read JSON data from {OUTPUT_PATH}")
    exit()

# Filter to the latest fetched
if "fetched" not in leaderboard_df.columns:
    print("Error: 'fetched' column missing from the data.")
    exit()

leaderboard_df["fetched"] = pd.to_datetime(leaderboard_df["fetched"]).dt.strftime('%Y-%m-%d')
latest_date = leaderboard_df["fetched"].max()
print(latest_date)
latest_data = leaderboard_df.query(f'fetched == "{latest_date}"')

# Create a histogram for player ratings
plt.figure(figsize=(10, 6))
plt.hist(latest_data['rating'], bins=range(0, 2200, 100), edgecolor='black', alpha=0.7)
plt.title(f'Distribution of player ratings', fontsize=16)
plt.xlabel('Rating ranges', fontsize=14)
plt.ylabel('Players count', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
histogram_path = VISUALS_PATH / "rating_distribution_histogram.png"
plt.savefig(histogram_path)
plt.show()

print(f"Histogram saved to {histogram_path}")
