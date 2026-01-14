import pandas as pd
import h3
import argparse
import os

def get_hex_safe(lat_lng_str, res):
    """Parses 'Lat, Lon' string and returns H3 index."""
    try:
        lat, lng = map(float, lat_lng_str.split(','))
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
    parser = argparse.ArgumentParser(description='Add hex centroids to presets.')
    parser.add_argument('preset_csv', nargs='?', default='preset_filtered.csv')
    parser.add_argument('output_csv', nargs='?', default='preset_with_centroids.csv')
    
    args = parser.parse_args()

    if not os.path.exists(args.preset_csv):
        print("Error: Input file not found.")
        return

    # Load Presets
    df = pd.read_csv(args.preset_csv)
    RES = 8

    print(f"Processing {len(df)} rows...")

    results = []
    for _, row in df.iterrows():
        p_hex = get_hex_safe(row['Popular Pickup Lat,Lon'], RES)
        d_hex = get_hex_safe(row['Popular Destination Lat, Lon'], RES)

        # Get Centroids
        p_lat, p_lon = get_centroid(p_hex)
        d_lat, d_lon = get_centroid(d_hex)
        
        # Create a dictionary of the original row plus new columns
        new_row = row.to_dict()
        new_row['pickup_hex8'] = p_hex
        new_row['destination_hex8'] = d_hex
        new_row['pickup_hex8_lat'] = p_lat
        new_row['pickup_hex8_lon'] = p_lon
        new_row['destination_hex8_lat'] = d_lat
        new_row['destination_hex8_lon'] = d_lon
        
        results.append(new_row)

    # Save Output
    output_df = pd.DataFrame(results)
    output_df.to_csv(args.output_csv, index=False)

    print(f"Done! Saved {len(output_df)} enriched routes to {args.output_csv}")

if __name__ == "__main__":
    main()