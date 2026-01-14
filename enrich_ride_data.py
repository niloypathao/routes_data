import pandas as pd
import h3
import argparse
import os

def get_hex_safe(lat, lng, res):
    """Converts coordinates to H3 ID."""
    try:
        if hasattr(h3, 'latlng_to_cell'):
            return h3.latlng_to_cell(lat, lng, res)
        return h3.geo_to_h3(lat, lng, res)
    except:
        return None

def get_centroid(hex_id):
    """Returns (lat, lon) of the hex center."""
    try:
        if hasattr(h3, 'cell_to_latlng'):
            return h3.cell_to_latlng(hex_id)
        return h3.h3_to_geo(hex_id)
    except:
        return (None, None)

def main():
    parser = argparse.ArgumentParser(description='Enrich ride data with hex IDs and centroids.')
    parser.add_argument('input_csv', nargs='?', default='preset_with_centroids.csv', help='Raw ride data')
    parser.add_argument('output_csv', nargs='?', default='enriched_rides_with_centroids.csv', help='Output file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_csv):
        print(f"Error: {args.input_csv} not found.")
        return

    print(f"Reading {args.input_csv}...")
    # Using specific columns to save memory
    df = pd.read_csv(args.input_csv)

    RES = 8
    print(f"Calculating Hex-{RES} IDs and Centroids...")

    # 1. Generate Hex IDs
    df['pickup_hex8'] = [get_hex_safe(lat, lng, RES) for lat, lng in zip(df['estimated_pickup_latitude'], df['estimated_pickup_longitude'])]
    df['dropoff_hex8'] = [get_hex_safe(lat, lng, RES) for lat, lng in zip(df['estimated_dropoff_latitude'], df['estimated_dropoff_longitude'])]

    # 2. Generate Pickup Centroids
    print("Mapping Pickup Centroids...")
    p_centroids = [get_centroid(h) for h in df['pickup_hex8']]
    df['pickup_centroid_lat'] = [c[0] for c in p_centroids]
    df['pickup_centroid_lon'] = [c[1] for c in p_centroids]

    # 3. Generate Dropoff Centroids
    print("Mapping Dropoff Centroids...")
    d_centroids = [get_centroid(h) for h in df['dropoff_hex8']]
    df['dropoff_centroid_lat'] = [c[0] for c in d_centroids]
    df['dropoff_centroid_lon'] = [c[1] for c in d_centroids]

    # 4. Save to CSV
    # We keep the original coordinates + new hex data
    cols_to_save = [
        'estimated_pickup_latitude', 'estimated_pickup_longitude',
        'estimated_dropoff_latitude', 'estimated_dropoff_longitude',
        'pickup_hex8', 'dropoff_hex8',
        'pickup_centroid_lat', 'pickup_centroid_lon',
        'dropoff_centroid_lat', 'dropoff_centroid_lon'
    ]
    
    print(f"Saving to {args.output_csv}...")
    df[cols_to_save].to_csv(args.output_csv, index=False)
    print("Successfully completed!")

if __name__ == "__main__":
    main()