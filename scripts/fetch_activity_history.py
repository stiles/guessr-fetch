import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
import squarify  # for treemap
from tqdm import tqdm
from config import cookies, headers  # requires personalized config file
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates

# Set the default font to Roboto
rcParams['font.family'] = 'Roboto'

def fetch_activity_data():
    """Fetch and paginate GeoGuessr activity data."""
    url = "https://www.geoguessr.com/api/v4/feed/friends"
    params = {"count": 100}
    all_entries = []
    pagination_token = None

    # Fetch all pages
    with tqdm(desc="Fetching activity history") as progress:
        while True:
            if pagination_token:
                params["paginationToken"] = pagination_token

            response = requests.get(url, params=params, cookies=cookies, headers=headers)
            response.raise_for_status()  # Raise error for bad responses
            data = response.json()

            # Add entries from current page
            entries = data.get("entries", [])
            all_entries.extend(entries)

            # Update pagination token
            pagination_token = data.get("paginationToken")
            if not pagination_token:
                break  # Stop if no more pages

            progress.update(len(entries))

    return all_entries

def parse_activity_to_dataframe(entries):
    """Parse activity entries into a structured Pandas DataFrame."""
    rows = []
    for entry in entries:
        try:
            activity_type = entry.get("type")  # Type of activity
            time = entry.get("time")  # Timestamp of activity
            user = entry.get("user", {}).get("nick")  # User nickname
            payload = entry.get("payload")  # Raw payload (can be JSON string or list)

            if isinstance(payload, str):
                # Safely parse JSON strings
                payload = json.loads(payload)

            # Process payloads into individual rows
            if isinstance(payload, list):
                for p in payload:
                    rows.append({
                        "type": activity_type,
                        "time": time,
                        "user": user,
                        "payload_type": p.get("type"),
                        "payload_time": p.get("time"),
                        "game_mode": p.get("payload", {}).get("gameMode"),
                        "competitive_mode": p.get("payload", {}).get("competitiveGameMode"),
                        "game_id": p.get("payload", {}).get("gameId"),
                        "map_slug": p.get("payload", {}).get("mapSlug"),
                        "map_name": p.get("payload", {}).get("mapName"),
                        "points": p.get("payload", {}).get("points"),
                    })
            else:
                rows.append({
                    "type": activity_type,
                    "time": time,
                    "user": user,
                    "payload_type": None,
                    "payload_time": None,
                    "game_mode": payload.get("gameMode"),
                    "competitive_mode": None,
                    "game_id": None,
                    "map_slug": payload.get("mapSlug"),
                    "map_name": payload.get("mapName"),
                    "points": payload.get("points"),
                })
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing entry: {entry}, Error: {e}")

    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # Fix dates
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df['date'] = df['time'].dt.date
    df = df.dropna(subset=['time'])
    df = df.sort_values(by='time')
    return df

def visualize_activity(activity_df):
    """Generate statistics and visualizations."""
    print("\n--- Statistics ---")
    # Count total activities
    total_activities = len(activity_df)
    print(f"Total activities: {total_activities}")

    # Count by game mode
    game_mode_counts = activity_df["game_mode"].value_counts()
    print("\nActivities by game mode:")
    print(game_mode_counts)

    # Count most-used maps
    map_counts = activity_df["map_name"].value_counts().head(7)
    print("\nMost used maps (Top 7):")
    print(map_counts)

    activity_df["date"] = pd.to_datetime(activity_df["time"].dt.date)  # Ensure 'date' is a datetime object
    activity_by_date = activity_df.groupby(["date", "game_mode"]).size().unstack(fill_value=0)

    # Bar chart for activity over time
    fig, ax = plt.subplots(figsize=(12, 6))
    activity_by_date.plot(kind="bar", stacked=True, colormap="Set2", ax=ax)
    ax.set_title("GeoGuessr activity over time, by type")
    ax.set_xlabel("")
    ax.set_ylabel("Count")

    # Fix x-axis formatting
    dates = activity_by_date.index
    tick_positions = [0, len(dates) // 4, len(dates) // 2, 3 * len(dates) // 4, len(dates) - 1]
    tick_labels = [dates[i].strftime("%b. %d, %Y") for i in tick_positions]

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=0)
    ax.legend(title="Mode")
    plt.tight_layout()
    plt.savefig("./visuals/charts/geoguessr_activity_chart.png")
    plt.show()

    # Treemap: Game Modes with "Other" category
    other_threshold = 5
    game_mode_counts['Other'] = game_mode_counts[game_mode_counts < other_threshold].sum()
    game_mode_counts = game_mode_counts[game_mode_counts >= other_threshold]
    
    plt.figure(figsize=(12, 6))
    squarify.plot(
        sizes=game_mode_counts,
        label=[f"{name}\n{count}" for name, count in game_mode_counts.items()],
        alpha=0.8,
        color=plt.cm.Set2.colors,
        pad=True,
    )
    plt.tight_layout()
    plt.axis("off")
    plt.title("Most-common GeoGuessr game modes")
    plt.savefig("./visuals/charts/game_modes_treemap.png")
    plt.show()

    # Treemap: Maps
    plt.figure(figsize=(12, 6))
    squarify.plot(
        sizes=map_counts,
        label=[f"{name}\n{count}" for name, count in map_counts.items()],
        alpha=0.8,
        color=plt.cm.Set2.colors,
        pad=True,
    )
    plt.tight_layout()
    plt.axis("off")
    plt.title("Most-used GeoGuessr maps")
    plt.savefig("./visuals/charts/maps_treemap.png")
    plt.show()

def main():
    # Fetch all activity data
    print("Fetching activity data...")
    activity_entries = fetch_activity_data()

    # Parse data into DataFrame
    print("Parsing activity data...")
    activity_df = parse_activity_to_dataframe(activity_entries)

    # Save the DataFrame to a JSON file
    output_file = "./data/activity/geoguessr_activity.json"
    
    activity_df['date'] = activity_df['date'].astype(str)
    activity_df.to_json(output_file, orient="records", indent=4)
    print(f"Activity data saved to '{output_file}'.")

    # Generate and display statistics and charts
    visualize_activity(activity_df)

if __name__ == "__main__":
    main()