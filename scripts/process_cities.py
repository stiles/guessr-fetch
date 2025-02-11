import os
import requests
import zipfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Paths
DATA_DIR = "data/geo/reference/large/"
ZIP_URL = "https://download.geonames.org/export/dump/cities5000.zip"
ZIP_PATH = os.path.join(DATA_DIR, "cities5000.zip")
TXT_PATH = os.path.join(DATA_DIR, "cities5000.txt")
JSON_OUTPUT_PATH = os.path.join(DATA_DIR, "geonames_all_world_cities_5000.json")
GEOJSON_OUTPUT_PATH = os.path.join(DATA_DIR, "geonames_all_world_cities_5000.geojson")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def download_and_extract():
    """Download and extract the cities5000.zip file."""
    if not os.path.exists(TXT_PATH):
        print("Downloading cities5000.zip...")
        response = requests.get(ZIP_URL, stream=True)
        with open(ZIP_PATH, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print("Download complete.")

        print("Extracting cities5000.txt...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)
        print("Extraction complete.")
    else:
        print("File already exists. Skipping download.")

def convert_to_geodataframe(df, output_path):
       """Convert a DataFrame into a GeoDataFrame and save as GeoJSON."""
       gdf = gpd.GeoDataFrame(
              df, geometry=[Point(lon, lat) for lat, lon in zip(df["lat"], df["lng"])], crs="EPSG:4326"
       )
       gdf.to_file(output_path, driver="GeoJSON")
       print(f"GeoJSON saved: {output_path}")

def process_geonames_data():
    """Read, process, and export the GeoNames dataset."""
    print("Processing GeoNames data...")

    # Define column names based on GeoNames format
    columns = [
        "geonameid", "city_name", "asciiname", "alternatenames",
        "lat", "lng", "feature_class", "feature_code",
        "country_code", "cc2", "admin1_code", "admin2_code",
        "admin3_code", "admin4_code", "population",
        "elevation", "dem", "timezone", "modification_date"
    ]

    # Load dataset
    df = pd.read_csv(TXT_PATH, sep="\t", names=columns, dtype={"admin1_code": str, "admin2_code": str}, keep_default_na=False)

    # Map country codes to country names (you may need a lookup for this)
    df["cntry_name"] = df["country_code"]  # Placeholder, ideally replaced with actual country names

    # Standardize admin_name field
    df["admin_name"] = df["admin1_code"]  # Placeholder, ideally replaced with actual admin names from a lookup

    # Select and rename relevant columns to align with your Street View script
    df = df.rename(columns={
        "lat": "lat",
        "lng": "lng",
        "city_name": "city_name",
        "admin_name": "admin_name",
        "country_code": "fips_cntry",  
        "cntry_name": "cntry_name",
    })

    # Sort by country name and city name
    df = df.sort_values(["cntry_name", "city_name"])

    # Save to JSON
    df.to_json(JSON_OUTPUT_PATH, orient="records", indent=4)
    print(f"Processed data saved to {JSON_OUTPUT_PATH}")

    # Convert to GeoDataFrame and save as GeoJSON
    geojson_output_path = GEOJSON_OUTPUT_PATH
    convert_to_geodataframe(df, geojson_output_path)

# Run the functions
download_and_extract()
process_geonames_data()