import requests
import pandas as pd
import geopandas as gpd
from pyproj import CRS, Transformer

# Esri Feature Service URL
BASE_URL = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/World_Cities/FeatureServer/0/query"

# Set source projection (likely Web Mercator)
SOURCE_CRS = CRS.from_epsg(3857)  # Web Mercator
TARGET_CRS = CRS.from_epsg(4326)  # WGS84
transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)

def fetch_esri_data(offset=0, limit=2000):
    """Fetch data from Esri Feature Service with pagination."""
    params = {
        "where": "1=1",  # No filtering yet
        "outFields": "*",  # Fetch all fields
        "f": "json",       # Return data as JSON
        "resultOffset": offset,  # Pagination offset
        "resultRecordCount": limit,  # Number of records to fetch
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()  # Raise an error for bad status codes
    data = response.json()
    return data.get("features", [])  # Return list of features

def fetch_all_data():
    """Fetch all data from the Esri Feature Service with pagination."""
    all_features = []
    offset = 0
    limit = 2000

    while True:
        print(f"Fetching records with offset {offset}...")
        features = fetch_esri_data(offset=offset, limit=limit)
        if not features:
            break  # Stop if no more data
        all_features.extend(features)
        offset += limit

    return all_features

def process_features(features):
    """Convert features to a Pandas DataFrame and filter by status."""
    # Extract attributes and geometry from features
    data = []
    for feature in features:
        attributes = feature["attributes"]
        geometry = feature.get("geometry", {})
        projected_x = geometry.get("x")
        projected_y = geometry.get("y")

        # Transform projected coordinates to geographic coordinates
        if projected_x is not None and projected_y is not None:
            lng, lat = transformer.transform(projected_x, projected_y)
            attributes["lng"] = lng
            attributes["lat"] = lat
        else:
            attributes["lng"] = None
            attributes["lat"] = None

        data.append(attributes)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.columns = df.columns.str.lower()

    # Filter for "National and provincial capital"
    filtered_df = df.query("status.str.contains('National')").drop(['port_id', 'label_flag', 'pop_source', 'objectid', 'pop_rank'], axis=1).copy()

    return filtered_df

# Main execution
if __name__ == "__main__":
    # Fetch all features
    features = fetch_all_data()

    # Process and filter features
    capitals_df = process_features(features)

    # Count and display results
    print(f"\nTotal cities fetched: {len(features)}")
    print(f"Total national capitals: {len(capitals_df)}")

    # Save the filtered capitals to a JSON file
    capitals_df.to_json("./data/geo/reference/national_capitals.json", indent=4, orient="records")
    print("Filtered capitals with coordinates saved to './data/geo/reference/national_capitals.json'.")
