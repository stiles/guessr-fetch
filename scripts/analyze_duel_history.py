#!/usr/bin/env python
# coding: utf-8
import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Base directory is the project root where the script is run
base_dir = os.getcwd()

# Paths relative to the project root
duels_json_path = os.path.join(base_dir, "data", "duels", "all", "stiles_duel_results.json")
countries_json_path = os.path.join(base_dir, "data", "geo", "reference", "countries_simple.json")
map_output_dir = os.path.join(base_dir, "visuals", "maps")
data_output_dir = os.path.join(base_dir, "data", "duels", 'analysis')


# Create the output directory if it doesn't exist
os.makedirs(map_output_dir, exist_ok=True)
os.makedirs(data_output_dir, exist_ok=True)

# Load duel history
duels_df = pd.read_json(duels_json_path)

# Convert to GeoDataFrame with round locations
round_locations_gdf = gpd.GeoDataFrame(
    duels_df,
    geometry=gpd.points_from_xy(duels_df.actual_lng, duels_df.actual_lat),
    crs="EPSG:4326",
)

# Load country boundaries
countries_gdf = gpd.read_file(countries_json_path)

# Filter out Antarctica
countries_gdf = countries_gdf[countries_gdf["ADMIN"] != "Antarctica"]

# Project to Robinson projection
countries_gdf_robinson = countries_gdf.to_crs("ESRI:54030")  # Robinson projection
round_locations_robinson = round_locations_gdf.to_crs("ESRI:54030")

# Plot the map
fig, ax = plt.subplots(figsize=(15, 10))
countries_gdf_robinson.plot(ax=ax, color="lightgray", edgecolor="white")
round_locations_robinson.plot(ax=ax, color="red", markersize=10, alpha=0.7)

# Clean up the plot
ax.set_title("GeoGuessr duels: Round locations", fontsize=15)
ax.axis("off")

# Save the map to the new directory
output_path = os.path.join(map_output_dir, "duel_rounds_map.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
print(f"Map saved successfully to {output_path}")

plt.show()

# ---- Group locations by country ----

# Perform spatial join to get country names for each point
joined_gdf = gpd.sjoin(round_locations_gdf, countries_gdf, how="left", predicate="within")

# Count points by country
country_counts = joined_gdf.groupby("ADMIN").size().reset_index(name="count")
country_counts = country_counts.sort_values(by="count", ascending=False)

# Save to CSV for further analysis
country_counts.to_json(f'{data_output_dir}/duel_counts_countries.json', indent=4, orient='records')