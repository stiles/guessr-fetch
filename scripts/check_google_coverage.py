import os
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def check_street_view_coverage_with_offsets(lat, lng, api_key, offsets=None):
    """Check if official Google Street View coverage exists, including nearby offsets."""
    offsets = offsets or [(0, 0)]
    url_template = (
        "https://maps.googleapis.com/maps/api/streetview/metadata"
        "?location={lat},{lng}&key={key}"
    )

    for offset_lat, offset_lng in offsets:
        try:
            query_lat = lat + offset_lat
            query_lng = lng + offset_lng
            url = url_template.format(lat=query_lat, lng=query_lng, key=api_key)
            response = requests.get(url)
            response.raise_for_status()
            metadata = response.json()
            status = metadata.get("status")
            copyright_info = metadata.get("copyright", "").strip().lower()

            # Official Google coverage
            if status == "OK" and "© google" in copyright_info:
                return metadata  # Return the first valid metadata
        except requests.exceptions.RequestException as e:
            print(f"Error querying offset ({offset_lat}, {offset_lng}): {e}")

    # Return no coverage if all offsets fail
    return {"status": "ZERO_RESULTS", "copyright": ""}

def fetch_country_coverage(countries_df, api_key):
    """Check Street View coverage for a list of countries."""
    results = []
    offsets = [
        (0, 0),         # Original
        (0.01, 0),      # North
        (-0.01, 0),     # South
        (0, 0.01),      # East
        (0, -0.01),     # West
    ]

    for _, row in countries_df.iterrows():
        country = row['cntry_name']
        city_name = row['city_name']
        admin_name = row['admin_name']
        lat, lng = row['lat'], row['lng']
        print(f"Checking coverage for {city_name}, {admin_name}, {country} at ({lat}, {lng}) with offsets...")
        metadata = check_street_view_coverage_with_offsets(lat, lng, api_key, offsets)

        # Extract metadata fields
        status = metadata.get("status", "")
        copyright_info = metadata.get("copyright", "").strip().lower()
        pano_id = metadata.get("pano_id", "N/A")  # Unique panorama identifier
        imagery_date = metadata.get("date", "Unknown")  # Date of imagery capture

        # Detect coverage sources
        has_google_copyright = "google" in copyright_info
        has_pano = pano_id != "N/A"

        # Classify the coverage type
        if status == "OK":
            if has_google_copyright:
                coverage_type = "Official Google"
            elif has_pano:
                coverage_type = "Non-Google (User-Contributed or Partner)"
            else:
                coverage_type = "Unknown Coverage"
        else:
            coverage_type = "No Coverage"

        # Append detailed metadata to results
        results.append({
            "country": country,
            "country_code_2": row['fips_cntry'],
            "capital_name": row['city_name'],
            # "country_code_3": row['gmi_admin'].split('-')[0],
            "lat": lat,
            "lng": lng,
            "coverage_google": has_google_copyright,
            "coverage_type": coverage_type,  # NEW FIELD
            "copyright": copyright_info,
            "date": imagery_date,
            "pano_id": pano_id,
        })
    
    return pd.DataFrame(results)


def estimate_street_view_generation(date):
    """Estimate the Google Street View camera generation based on imagery date."""
    if not date or date == "Unknown":
        return "No Coverage"
    year = int(date.split("-")[0])
    if year < 2009:
        return "Generation 1"
    elif year < 2012:
        return "Generation 2"
    elif year < 2017:
        return "Generation 3"
    else:
        return "Generation 4+"


def convert_to_geodataframe(df, output_path):
    """Convert a DataFrame into a GeoDataFrame and save as GeoJSON."""
    gdf = gpd.GeoDataFrame(
        df, geometry=[Point(lon, lat) for lat, lon in zip(df["lat"], df["lng"])], crs="EPSG:4326"
    )
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"GeoJSON saved: {output_path}")


# API Key
api_key = os.getenv("GEOGUESSR_API_KEY")

# Dataset of world capitals
countries_src = pd.read_json('./data/geo/reference/large/geonames_all_world_cities_5000.json').sort_values('cntry_name')
countries_df = countries_src.query('country_code_2 != "CN"').copy()  # Exclude China

# Check Street View coverage
coverage_df = fetch_country_coverage(countries_df, api_key)

# Apply this function to classify generations in your DataFrame:
coverage_df["generation"] = coverage_df["date"].apply(estimate_street_view_generation)

# Save results to a JSON file
json_output_path = "./data/geo/reference/official_street_view_coverage.json"
coverage_df.to_json(json_output_path, indent=4, orient='records')

# Convert to GeoDataFrame and save as GeoJSON
geojson_output_path = "./data/geo/reference/official_street_view_coverage.geojson"
convert_to_geodataframe(coverage_df, geojson_output_path)

types_df = coverage_df.generation.value_counts()

# Print the results
print("---")
print("Results collected.")
print(f"Types found: {types_df}")