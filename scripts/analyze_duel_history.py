#!/usr/bin/env python
# coding: utf-8

import us
import os
import json
import requests
import pandas as pd
import altair as alt
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Set the default font to Roboto
rcParams['font.family'] = 'Roboto'

# Date strings for storage
eastern = pytz.timezone("America/New_York")
today = datetime.now(eastern).strftime("%Y-%m-%d")

# Define paths relative to the script's directory
BASE_DIR = Path(__file__).resolve().parent.parent  # Root of the project
INPUT_PATH = BASE_DIR / "data" / "duels" / "all" / "stiles_duel_results.json"
OUTPUT_PATH = BASE_DIR / 'data' / 'duels'/'analysis'/'duel_counts_countries.json'

username = "stiles"

# Read the duel history as a DataFrame
duels_df = pd.read_json(INPUT_PATH)

# Process create timestamp as a date
duels_df["date"] = pd.to_datetime(duels_df["created"]).dt.date


# How many miles off are you, on average?
user_mean_guess_distance = round(duels_df.my_guess_miles.mean())
user_mean_guess_distance


# What was the worst guess in miles?
worst_guess = duels_df.my_guess_miles.max()
print(f"You're worst guess was {worst_guess} miles")


# What was the best guess?
best_guess = duels_df.my_guess_miles.min()
print('---')
print(f"You're worst guess was {best_guess} miles")

# ---

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

# Load a world shapefile or GeoJSON
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

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
fig, ax = plt.subplots(1, 1, figsize=(15, 10))
world.boundary.plot(ax=ax, linewidth=1)
duel_countries_gdf.plot(column="name", ax=ax, markersize=5, color="red", alpha=0.5, legend=True)
plt.title("GeoGuessr duel locations, by country", fontsize=16)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig(BASE_DIR / "visuals" / "maps" / "duel_locations_world_map.png")
plt.show()
