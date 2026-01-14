import pandas as pd
import h3
import argparse
import os

def get_hex_safe(lat, lng, res):
    """
    Converts lat/lng to H3 index. Returns None if coordinates are invalid.
    """
    try:
        # Supports both h3-py v3 and v4
        if hasattr(h3, 'latlng_to_cell'):
            return h3.latlng_to_cell(lat, lng, res)
        return h3.geo_to_h3(lat, lng, res)
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description='Add H3 Hex columns to existing ride data.')
    parser.add_argument('input_csv', nargs='?', default='big-data.csv', help='Input CSV filename')
    parser.add_argument('output_csv', nargs='?', default='big-data-with-hex.csv', help='Output CSV filename')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_csv):
        print(f"Error: {args.input_csv} not found.")
        return

    print(f"Reading {args.input_csv}...")
    
    # We use chunksize if the file is massive, but for standard files, 
    # reading the whole thing is faster.
    df = pd.read_csv(args.input_csv)

    RESOLUTION = 9

    print("Calculating Pickup Hexes...")
    df['pickup_hex_9'] = [
        get_hex_safe(lat, lng, RESOLUTION) 
        for lat, lng in zip(df['estimated_pickup_latitude'], df['estimated_pickup_longitude'])
    ]

    print("Calculating Dropoff Hexes...")
    df['dropoff_hex_9'] = [
        get_hex_safe(lat, lng, RESOLUTION) 
        for lat, lng in zip(df['estimated_dropoff_latitude'], df['estimated_dropoff_longitude'])
    ]

    print(f"Saving enriched data to {args.output_csv}...")
    df.to_csv(args.output_csv, index=False)
    print("Done!")

if __name__ == "__main__":
    main()