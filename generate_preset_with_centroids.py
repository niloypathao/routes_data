import pandas as pd
import h3
import argparse
import os

def get_hex_safe(lat_or_str, lng_or_res, res=None):
    """
    Converts lat/lng to H3 index. Handles both (lat, lng) floats and "lat,lng" string.
    """
    if res is None:
        # lat_or_str is string "lat,lng", lng_or_res is res
        lat_lng_str = lat_or_str
        res = lng_or_res
        lat, lng = map(float, lat_lng_str.split(','))
    else:
        lat = lat_or_str
        lng = lng_or_res
    
    try:
        # Supports both h3-py v3 and v4
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
    parser = argparse.ArgumentParser(description='Generate preset_with_centroids.csv from preset.csv and big-data.csv')
    parser.add_argument('preset_csv', nargs='?', default='preset.csv', help='Input preset CSV file')
    parser.add_argument('big_data_csv', nargs='?', default='big-data.csv', help='Input big-data CSV file')
    parser.add_argument('output_csv', nargs='?', default='preset_with_centroids.csv', help='Output CSV file')
    parser.add_argument('--min_rides', type=int, default=5, help='Minimum number of rides to keep a route')
    parser.add_argument('--resolution', type=int, default=8, help='H3 resolution for hexes')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.preset_csv):
        print(f"Error: {args.preset_csv} not found.")
        return
    if not os.path.exists(args.big_data_csv):
        print(f"Error: {args.big_data_csv} not found.")
        return

    print(f"Reading {args.big_data_csv}...")
    df = pd.read_csv(args.big_data_csv)

    RES = args.resolution
    print(f"Processing coordinates into Hex-{RES}...")
    
    # Calculate hexes
    df[f'p_hex{RES}'] = [get_hex_safe(lat, lng, RES) for lat, lng in zip(df['estimated_pickup_latitude'], df['estimated_pickup_longitude'])]
    df[f'd_hex{RES}'] = [get_hex_safe(lat, lng, RES) for lat, lng in zip(df['estimated_dropoff_latitude'], df['estimated_dropoff_longitude'])]

    print("Aggregating route counts...")
    # Group and count
    route_counts = df.groupby([f'p_hex{RES}', f'd_hex{RES}']).size().reset_index(name='ride_count')
    
    # Filter low-volume routes
    initial_count = len(route_counts)
    route_counts = route_counts[route_counts['ride_count'] >= args.min_rides]
    filtered_count = len(route_counts)
    
    print(f"Hex-8 Results:")
    print(f"- Total unique routes found: {initial_count}")
    print(f"- Routes remaining after filtering (>= {args.min_rides} rides): {filtered_count}")
    print(f"- Reduction: {initial_count - filtered_count} low-volume routes removed.")

    # Create a set of valid routes
    valid_routes = set(zip(route_counts[f'p_hex{RES}'], route_counts[f'd_hex{RES}']))

    # Now process presets
    print("Reading preset data...")
    preset_df = pd.read_csv(args.preset_csv)

    print("Mapping presets to Hex-8 and filtering...")
    
    def is_route_valid(row):
        # Convert the string columns to hex IDs
        p_hex = get_hex_safe(row['Popular Pickup Lat,Lon'], RES)
        d_hex = get_hex_safe(row['Popular Destination Lat, Lon'], RES)
        
        # Check if this specific pair exists in our "Power Lanes"
        return (p_hex, d_hex) in valid_routes

    # Apply the filter
    initial_preset_count = len(preset_df)
    filtered_df = preset_df[preset_df.apply(is_route_valid, axis=1)].copy()
    final_preset_count = len(filtered_df)

    # Add hex columns to filtered_df
    filtered_df[f'pickup_hex{RES}'] = [get_hex_safe(row['Popular Pickup Lat,Lon'], RES) for _, row in filtered_df.iterrows()]
    filtered_df[f'destination_hex{RES}'] = [get_hex_safe(row['Popular Destination Lat, Lon'], RES) for _, row in filtered_df.iterrows()]

    # Remove duplicates based on hex pairs to avoid redundant centroids
    filtered_df = filtered_df.drop_duplicates(subset=[f'pickup_hex{RES}', f'destination_hex{RES}'])

    print("\n--- Filtering Summary ---")
    print(f"Original Presets: {initial_preset_count}")
    print(f"Presets kept after hex filter: {final_preset_count}")
    print(f"Unique hex pairs: {len(filtered_df)}")
    print(f"Duplicates removed: {final_preset_count - len(filtered_df)}")

    # Now add centroids
    print("Adding centroids...")
    results = []
    for _, row in filtered_df.iterrows():
        p_hex = row[f'pickup_hex{RES}']
        d_hex = row[f'destination_hex{RES}']

        # Get Centroids
        p_lat, p_lon = get_centroid(p_hex)
        d_lat, d_lon = get_centroid(d_hex)
        
        # Create a dictionary of the original row plus new columns
        new_row = row.to_dict()
        new_row[f'pickup_hex{RES}_lat'] = p_lat
        new_row[f'pickup_hex{RES}_lon'] = p_lon
        new_row[f'destination_hex{RES}_lat'] = d_lat
        new_row[f'destination_hex{RES}_lon'] = d_lon
        
        results.append(new_row)

    # Save Output
    output_df = pd.DataFrame(results)
    output_df.to_csv(args.output_csv, index=False)

    print(f"Done! Saved {len(output_df)} enriched routes to {args.output_csv}")

if __name__ == "__main__":
    main()