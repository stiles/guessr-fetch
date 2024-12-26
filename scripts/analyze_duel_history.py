#!/usr/bin/env python
# coding: utf-8

import os
import json
import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
from matplotlib import rcParams
from zipfile import ZipFile

# Set the default font to Roboto
rcParams['font.family'] = 'Roboto'

# Date strings for storage
eastern = pytz.timezone("America/New_York")
today = datetime.now(eastern).strftime("%Y-%m-%d")

username = "stiles"

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
INPUT_PATH = BASE_DIR / "data" / "duels" / "all" / f"{username}_duel_results.json"
OUTPUT_PATH = BASE_DIR / 'data' / 'duels'/'analysis'/'duel_counts_countries.json'

# Read the duel history as a DataFrame
duels_df = pd.read_json(INPUT_PATH)

# Process create timestamp as a date
duels_df["date"] = pd.to_datetime(duels_df["created"], format='mixed').dt.date

# How many miles off are you, on average?
user_mean_guess_distance = round(duels_df.my_guess_miles.mean())

# What was the worst guess in miles?
worst_guess = duels_df.my_guess_miles.max()
print(f"You're worst guess was {worst_guess} miles")


# What was the best guess?
best_guess = duels_df.my_guess_miles.min()
print('---')
print(f"You're best guess was {best_guess} miles")

# Filter the dataframe for unique duel IDs
outcomes_df = duels_df[["duel_id", "duel_outcome", "duel_opponent"]].drop_duplicates()

# What's my record?
record_df = outcomes_df.duel_outcome.value_counts().reset_index()
total_games = record_df["count"].sum()
record_df["outcome_pct"] = round((record_df["count"] / total_games) * 100, 2)
print('---')
print(record_df)

# Geography
round_locations_gdf = gpd.GeoDataFrame(
    duels_df,
    geometry=gpd.points_from_xy(duels_df.actual_lng, duels_df.actual_lat),
    crs="EPSG:4326",
)

# Download from Natural Earth and save locally

# Path to the local directory for geo data
geo_data_dir = BASE_DIR / "data" / "geo" / "reference"
geo_data_dir.mkdir(parents=True, exist_ok=True)

# Path to the ZIP file and extracted shapefile
zip_path = geo_data_dir / "naturalearth_lowres.zip"
shapefile_path = geo_data_dir / "ne_110m_admin_0_countries.shp"

# Download and extract the Natural Earth data if not already done
if not shapefile_path.exists():
    print("Downloading and extracting Natural Earth data...")
    url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    response = requests.get(url)
    with open(zip_path, "wb") as file:
        file.write(response.content)

    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(geo_data_dir)

# Read the shapefile using GeoPandas
world = gpd.read_file(shapefile_path).rename(columns={'SOVEREIGNT': 'name'})

# Spatial join to count duels by country
duel_countries_gdf = gpd.sjoin(round_locations_gdf, world, how="left", predicate="within")
country_counts = duel_countries_gdf.groupby("name").size().reset_index(name="duel_count")
country_counts = country_counts.sort_values(by="duel_count", ascending=False)

# Top 10 countries
top_10_countries = country_counts.head(10)
print("\nTop 10 countries by duel count:")
print(country_counts)

country_counts.to_json(OUTPUT_PATH, indent=4, orient='records')

# Map visualization

# Clip out Antarctica
world = world[world['name'] != 'Antarctica']

# Transform to Robinson projection
world = world.to_crs("ESRI:54030")
duel_countries_gdf = duel_countries_gdf.to_crs("ESRI:54030")

# Enhanced Map Visualization
fig, ax = plt.subplots(1, 1, figsize=(15, 10))

# Plot world boundaries with Robinson projection
world.plot(
    ax=ax,
    color="lightgray",     # Light gray fill color for countries
    edgecolor="white",     # White borders
    linewidth=0.5          # Border width
)

# Plot duel locations
duel_countries_gdf.plot(
    ax=ax,
    markersize=2,  # Adjust size for better visibility
    color="#c52622",
    alpha=0.7,
    legend=False
)

# Dynamic title
plt.title(f"{username.title()} GeoGuessr duels: All round locations", fontsize=18, fontweight="bold")

# Remove axis ticks and border
ax.axis("off")

# Save the Enhanced Map
output_map_path = BASE_DIR / "visuals" / "maps" / "duel_locations_world_map.png"
plt.tight_layout()
plt.savefig(output_map_path)
plt.show()