import os
import requests
import geopandas as gpd
import matplotlib.pyplot as plt
from rich import print

# Fetch the API key from the environment
google_maps_api_key = os.getenv("GEOGUESSR_API_KEY")

# Ensure the key is available
if not google_maps_api_key:
    raise ValueError("Google Maps API Key not found in the environment!")

# Headers for the request
headers = {
    'sec-ch-ua-platform': '"macOS"',
    'X-User-Agent': 'grpc-web-javascript/0.1',
    'Referer': 'https://www.geoguessr.com/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'X-Goog-Maps-Channel-Id': '',
    'sec-ch-ua-mobile': '?0',
    'X-Goog-Api-Key': google_maps_api_key,
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Content-Type': 'application/json+protobuf',
}

# Define the ID
location_id = "Gh1N2VhnOaziKblRvU3hRg"

# Request payload
data = f'[["apiv3",null,null,null,"US",null,null,null,null,null,[[0]]],["en"],[[[2,"{location_id}"]]],[[1,2,3,4,8,6]]]'

# Make the request
response = requests.post(
    'https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/GetMetadata',
    headers=headers,
    data=data,
)

# Parse the response JSON
response_json = response.json()

# Extract location
try:
    location = response_json[1][0][3][2][1][0]
    coordinates = (
        response_json[1][0][5][0][1][0][2],  # Longitude
        response_json[1][0][5][0][1][0][3],  # Latitude
    )
    print(f"Location: {location}")
    print(f"Coordinates: {coordinates}")

    # --- Visualize on a map ---
    
    # Load a world map from Geopandas
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # Convert the world map to Web Mercator (EPSG:3857)
    world = world.to_crs(epsg=3857)

    # Create a GeoDataFrame for the red dot
    # Create a GeoDataFrame for the red dot
    point_gdf = gpd.GeoDataFrame(
        {'geometry': [gpd.points_from_xy([coordinates[1]], [coordinates[0]])[0]]},  # Swap lat, lng
        crs="EPSG:4326"
    ).to_crs(epsg=3857)  # Convert to Web Mercator

    # Plot the map
    fig, ax = plt.subplots(figsize=(12, 8))
    world.plot(ax=ax, color='lightgray', edgecolor='white')
    point_gdf.plot(ax=ax, color='red', markersize=10)

    # Clip the map to exclude poles
    ax.set_xlim([-20026376.39, 20026376.39])  # Full Web Mercator extent in x
    ax.set_ylim([-10000000, 10000000])  # Limit y extent to clip poles

    # Add title and labels
    ax.set_title(f"Location: {location}\nCoordinates: {coordinates}", fontsize=15)
    ax.axis("off")

    # Show the plot
    plt.tight_layout()
    plt.show()

except (IndexError, TypeError) as e:
    print("Error extracting data:", e)
