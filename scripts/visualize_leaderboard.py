import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import rcParams

today = pd.Timestamp('today').strftime('%b. %d, %Y')
print(today)

username = 'stiles'

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

# Check if the username exists in the data
user_rating = latest_data.loc[latest_data['nick'] == username, 'rating']
user_rating = user_rating.iloc[0] if not user_rating.empty else None

# Create a histogram for player ratings
plt.figure(figsize=(10, 6))
plt.hist(latest_data['rating'], bins=range(0, 2200, 100), edgecolor='black', alpha=0.7, label="Ratings Distribution")
plt.suptitle(f'Distribution of GeoGuesser ratings on global leaderboard — {today}',fontsize=16, y=.97)
plt.title('Higher ratings represent greater skill in the game',fontsize=12)
plt.xlabel('Ratings', fontsize=12)
plt.ylabel('Number of players', fontsize=12)

# Add a gray anno line for the username's rating if it exists
if user_rating is not None:
    plt.axvline(user_rating, color='#b1b1b1', linestyle='--', linewidth=2, label=f"{username}'s rating: {user_rating}")
else:
    print(f"Warning: Username '{username}' not found in the latest data.")

plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save the histogram
histogram_path = VISUALS_PATH / "rating_distribution_histogram.png"
plt.savefig(histogram_path)
plt.show()

print(f"Histogram saved to {histogram_path}")
