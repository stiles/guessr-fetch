import os
import requests
import pandas as pd

def check_street_view_coverage_with_offsets(lat, lng, api_key, offsets=None):
    """Check if official Google Street View coverage exists, including nearby offsets."""
    offsets = offsets or [(0, 0)]  # Default is the original point
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
        (0, 0),         # Original point
        (0.01, 0),      # North
        (-0.01, 0),     # South
        (0, 0.01),      # East
        (0, -0.01),     # West
    ]

    for _, row in countries_df.iterrows():
        country = row['cntry_name']
        lat, lng = row['lat'], row['lng']
        print(f"Checking coverage for {country} at ({lat}, {lng}) with offsets...")
        metadata = check_street_view_coverage_with_offsets(lat, lng, api_key, offsets)

        # Parse metadata for detailed results
        status = metadata.get("status")
        copyright_info = metadata.get("copyright", "")
        covered = status == "OK" and "© google" in copyright_info

        # Append detailed metadata to results
        results.append({
            "country": country,
            "country_code_2": row['fips_cntry'],
            "capital_name": row['city_name'],
            "country_code_3": row['gmi_admin'].split('-')[0],
            "lat": lat,
            "lng": lng,
            "coverage_google": covered,
            "copyright": copyright_info,
            "date": metadata.get("date"),
        })
    return pd.DataFrame(results)

# API Key
api_key = os.getenv("GOOGLE_STREET_VIEW_STATIC_API")

# Dataset of world capitals
countries_df = pd.read_json('./data/geo/reference/national_capitals.json')

# Check Street View coverage
coverage_df = fetch_country_coverage(countries_df, api_key)

# Save results to a JSON file
coverage_df.to_json("./data/geo/reference/official_street_view_coverage.json", indent=4, orient='records')

# Print the results
print("\nDetailed Street View Coverage Results:")
print(coverage_df)