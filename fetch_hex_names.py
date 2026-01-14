import pandas as pd
import requests
import json
import argparse
import os
from concurrent.futures import ThreadPoolExecutor

# API Configuration
API_URL = "http://34.80.56.250:8080/api/v1/shortaddress"
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'nisuecb'
}

# Cache to avoid calling the same coordinates twice
address_cache = {}

def get_short_address(lat, lon):
    """Calls the API to get the English short address. Returns None if failed."""
    coord_key = (round(lat, 6), round(lon, 6))
    
    if coord_key in address_cache:
        return address_cache[coord_key]

    payload = json.dumps({
        "1": {
            "location": {
                "lat": lat,
                "lon": lon
            }
        }
    })

    try:
        response = requests.post(API_URL, headers=HEADERS, data=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            address = data.get("1", {}).get("short_address", {}).get("en")
            # Only cache if it's a valid string, otherwise store None
            if address and address.strip():
                address_cache[coord_key] = address
                return address
    except Exception as e:
        print(f"Error fetching address for {lat}, {lon}: {e}")
    
    address_cache[coord_key] = None
    return None

def main():
    parser = argparse.ArgumentParser(description='Fetch hex names for centroids.')
    parser.add_argument('input_csv', nargs='?', default='preset_with_centroids.csv')
    parser.add_argument('output_csv', nargs='?', default='preset_with_names.csv')
    
    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        print(f"Error: {args.input_csv} not found.")
        return

    print(f"Loading {args.input_csv}...")
    df = pd.read_csv(args.input_csv)

    # 1. Get unique points
    unique_pickups = df[['pickup_hex8_lat', 'pickup_hex8_lon']].drop_duplicates()
    unique_dropoffs = df[['destination_hex8_lat', 'destination_hex8_lon']].drop_duplicates()
    all_unique_points = pd.concat([
        unique_pickups.rename(columns={'pickup_centroid_lat': 'lat', 'pickup_centroid_lon': 'lon'}),
        unique_dropoffs.rename(columns={'dropoff_centroid_lat': 'lat', 'dropoff_centroid_lon': 'lon'})
    ]).drop_duplicates()

    print(f"Querying {len(all_unique_points)} unique centroids...")

    # 2. Fetch names with Threading
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda p: get_short_address(p[0], p[1]), all_unique_points.values)

    # 3. Map names
    print("Mapping names and filtering...")
    df['pickup_area_name'] = df.apply(
        lambda row: address_cache.get((round(row['pickup_hex8_lat'], 6), round(row['pickup_hex8_lon'], 6))), 
        axis=1
    )
    df['dropoff_area_name'] = df.apply(
        lambda row: address_cache.get((round(row['destination_hex8_lat'], 6), round(row['destination_hex8_lon'], 6))), 
        axis=1
    )

    # 4. Save all rows, including unknowns
    df.to_csv(args.output_csv, index=False)
    
    print("\n--- Results ---")
    print(f"Total rides processed: {len(df)}")
    print(f"Final file saved as: {args.output_csv}")

if __name__ == "__main__":
    main()