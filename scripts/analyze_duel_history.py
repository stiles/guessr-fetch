#!/usr/bin/env python
# coding: utf-8

import us
import os
import json
import requests
import pandas as pd
import jupyter_black
import altair as alt
import geopandas as gpd


jupyter_black.load()
pd.options.display.max_columns = 100
pd.options.display.max_rows = 100
pd.options.display.max_colwidth = None


username = "stiles"


# ---

# Read the duel history as a DataFrame
duels_df = pd.read_json("../data/duels/all/stiles_duel_results.json")


# Process create timestamp as a date
duels_df["date"] = pd.to_datetime(duels_df["created"]).dt.date


duels_df.head()


# How many miles off are you, on average?
user_mean_guess_distance = round(duels_df.my_guess_miles.mean())
user_mean_guess_distance


# What was the worst guess in miles?
worst_guess = duels_df.my_guess_miles.max()
worst_guess


# What was the best guess?
best_guess = duels_df.my_guess_miles.min()
best_guess


# ---

# Filter the dataframe for unique duel IDs
outcomes_df = duels_df[["duel_id", "duel_outcome", "duel_opponent"]].drop_duplicates()
outcomes_df.head()


# What's my record?
record_df = outcomes_df.duel_outcome.value_counts().reset_index()
total_games = record_df["count"].sum()
record_df["outcome_pct"] = round((record_df["count"] / total_games) * 100, 2)
record_df


# ---

# Geography


round_locations_gdf = gpd.GeoDataFrame(
    duels_df,
    geometry=gpd.points_from_xy(duels_df.actual_lng, duels_df.actual_lat),
    crs="EPSG:4326",
)


round_locations_gdf.plot()


get_ipython().system('jupyter nbconvert --to script --no-prompt --output ../scripts/analyze_duel_history analyze_duels.ipynb')




