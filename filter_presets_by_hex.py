import pandas as pd
import h3
import argparse
import os

def get_hex_safe(lat_lng_str, res):
    """
    Parses a 'Lat, Lon' string and converts to H3 index.
    """
    try:
        # Split the string "23.73, 90.41" into floats
        lat, lng = map(float, lat_lng_str.split(','))
        if hasattr(h3, 'latlng_to_cell'):
            return h3.latlng_to_cell(lat, lng, res)
        return h3.geo_to_h3(lat, lng, res)
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description='Filter preset routes based on high-volume Hex-8 corridors.')
    parser.add_argument('preset_csv', nargs='?', default='preset.csv', help='The preset route file')
    parser.add_argument('hex_filter_csv', nargs='?', default='hex8_route_counts_filtered.csv', help='The filtered hex pairs')
    parser.add_argument('output_csv', nargs='?', default='preset_filtered.csv', help='Output filename')
    
    args = parser.parse_args()

    # Check if files exist
    if not os.path.exists(args.preset_csv) or not os.path.exists(args.hex_filter_csv):
        print("Error: Ensure both preset.csv and hex8_route_counts_filtered.csv exist.")
        return

    # 1. Load the Filter (The high-volume hex pairs)
    print("Loading hex filters...")
    filter_df = pd.read_csv(args.hex_filter_csv)
    # Create a set of tuples {(pickup_hex, dropoff_hex), ...} for lightning fast lookup
    valid_routes = set(zip(filter_df['p_hex8'], filter_df['d_hex8']))

    # 2. Load the Presets
    print("Reading preset data...")
    preset_df = pd.read_csv(args.preset_csv)

    RES = 8
    
    # 3. Process Presets and Filter
    print("Mapping presets to Hex-8 and filtering...")
    
    def is_route_valid(row):
        # Convert the string columns to hex IDs
        p_hex = get_hex_safe(row['Popular Pickup Lat,Lon'], RES)
        d_hex = get_hex_safe(row['Popular Destination Lat, Lon'], RES)
        
        # Check if this specific pair exists in our "Power Lanes"
        return (p_hex, d_hex) in valid_routes

    # Apply the filter
    initial_count = len(preset_df)
    filtered_df = preset_df[preset_df.apply(is_route_valid, axis=1)].copy()
    final_count = len(filtered_df)

    # 4. Save results
    filtered_df.to_csv(args.output_csv, index=False)

    print("\n--- Filtering Summary ---")
    print(f"Original Presets: {initial_count}")
    print(f"Presets kept:     {final_count}")
    print(f"Presets removed:  {initial_count - final_count}")
    print(f"Saved to:         {args.output_csv}")

if __name__ == "__main__":
    main()