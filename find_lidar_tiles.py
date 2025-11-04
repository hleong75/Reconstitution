#!/usr/bin/env python3
"""
Helper script to identify IGN LiDAR tiles needed for a location.
This helps users manually download the correct tiles from IGN Geoservices.
"""

import sys
import yaml
import argparse

# Configuration constants
IGN_TILE_SIZE_KM = 1.0  # IGN LiDAR tiles are 1km x 1km
TILE_SIZE_METERS = 1000  # Tile size in meters for coordinate conversion
TILE_GRID_PADDING = 1  # Additional tiles to check beyond calculated radius

# Approximate coordinate conversion constants (for fallback when pyproj unavailable)
# These are rough approximations for France only and should not be used for precise work
# Based on approximate center of France (lon ~2.5°E, lat ~46.5°N)
LAMBERT93_APPROX_X_OFFSET = 600000  # Approximate X offset in meters
LAMBERT93_APPROX_Y_OFFSET = 6800000  # Approximate Y offset in meters
LAMBERT93_APPROX_LON_REF = 2.5  # Reference longitude for approximation
LAMBERT93_APPROX_LAT_REF = 46.5  # Reference latitude for approximation
LAMBERT93_APPROX_LON_SCALE = 100000  # Meters per degree longitude (rough)
LAMBERT93_APPROX_LAT_SCALE = 110000  # Meters per degree latitude (rough)


def wgs84_to_lambert93(lat, lon):
    """
    Convert WGS84 coordinates to Lambert 93 (French national projection)
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Tuple of (x, y) in Lambert 93 meters
    """
    try:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
        x, y = transformer.transform(lon, lat)
        return x, y
    except ImportError:
        print("Warning: pyproj not installed, using approximate conversion")
        print("Install pyproj for accurate results: pip install pyproj")
        # Very rough approximation for France only
        # NOT accurate for precise work - install pyproj for real conversions
        x = LAMBERT93_APPROX_X_OFFSET + (lon - LAMBERT93_APPROX_LON_REF) * LAMBERT93_APPROX_LON_SCALE
        y = LAMBERT93_APPROX_Y_OFFSET + (lat - LAMBERT93_APPROX_LAT_REF) * LAMBERT93_APPROX_LAT_SCALE
        return x, y


def get_tiles_for_location(lat, lon, radius_km=10):
    """
    Get list of LiDAR tile coordinates for a location
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers
        
    Returns:
        List of (tile_x, tile_y) tuples
    """
    # Convert to Lambert 93
    x, y = wgs84_to_lambert93(lat, lon)
    
    # Tiles are 1km x 1km, named by lower-left corner in km
    center_tile_x = int(x / TILE_SIZE_METERS)
    center_tile_y = int(y / TILE_SIZE_METERS)
    
    # Calculate tiles in radius
    tiles_per_side = int(radius_km / IGN_TILE_SIZE_KM) + TILE_GRID_PADDING
    tiles = []
    
    for dx in range(-tiles_per_side, tiles_per_side + 1):
        for dy in range(-tiles_per_side, tiles_per_side + 1):
            # Check if tile is within radius
            dist_km = ((dx * dx + dy * dy) ** 0.5)
            if dist_km <= radius_km:
                tile_x = center_tile_x + dx
                tile_y = center_tile_y + dy
                tiles.append((tile_x, tile_y))
    
    return x, y, center_tile_x, center_tile_y, tiles


def main():
    parser = argparse.ArgumentParser(
        description='Find IGN LiDAR tiles for a location',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use location from config.yaml
  python find_lidar_tiles.py
  
  # Specify custom location
  python find_lidar_tiles.py --lat 48.6439 --lon 1.8294 --radius 5
  
  # Get help
  python find_lidar_tiles.py --help
"""
    )
    
    parser.add_argument('--lat', type=float, help='Latitude in decimal degrees')
    parser.add_argument('--lon', type=float, help='Longitude in decimal degrees')
    parser.add_argument('--radius', type=float, help='Radius in kilometers')
    parser.add_argument('--config', default='config.yaml', help='Config file path (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Load from config if not specified
    if args.lat is None or args.lon is None:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
            
            location = config.get('location', {})
            lat = args.lat or location.get('center_lat')
            lon = args.lon or location.get('center_lon')
            radius_km = args.radius or location.get('radius_km', 10)
            location_name = location.get('name', 'Unknown')
        except FileNotFoundError:
            print(f"Error: Config file '{args.config}' not found")
            print("Please specify --lat, --lon, and --radius arguments")
            sys.exit(1)
    else:
        lat = args.lat
        lon = args.lon
        radius_km = args.radius or 10
        location_name = f"{lat}, {lon}"
    
    print("=" * 70)
    print("IGN LiDAR HD Tile Finder")
    print("=" * 70)
    print()
    print(f"Location: {location_name}")
    print(f"WGS84 Coordinates: {lat:.6f}°N, {lon:.6f}°E")
    print(f"Search Radius: {radius_km} km")
    print()
    
    # Get tiles
    x, y, center_x, center_y, tiles = get_tiles_for_location(lat, lon, radius_km)
    
    print(f"Lambert 93 Coordinates: X={x:.2f}m, Y={y:.2f}m")
    print(f"Center Tile: {center_x}, {center_y}")
    print()
    
    print(f"Number of tiles needed: {len(tiles)}")
    print()
    
    # Print tile list
    print("Tile Coordinates (X, Y):")
    print("-" * 70)
    for tile_x, tile_y in sorted(tiles):
        filename = f"LHD_FXX_{tile_x:04d}_{tile_y:04d}_PTS_C_LAMB93_IGN69.copc.laz"
        print(f"  Tile: {tile_x:04d}, {tile_y:04d}  →  {filename}")
    
    print()
    print("=" * 70)
    print("Manual Download Instructions")
    print("=" * 70)
    print()
    print("1. Visit one of these IGN portals:")
    print("   - https://geoservices.ign.fr/lidarhd (traditional portal)")
    print("   - https://data.geopf.fr/ (new platform)")
    print()
    print("2. Search for your location:")
    print(f"   - Name: {location_name}")
    print(f"   - Coordinates: {lat:.6f}, {lon:.6f}")
    print()
    print("3. Download tiles covering your area (see list above)")
    print()
    print("4. Place downloaded .copc.laz files in: data/lidar/")
    print()
    print("Note: Each tile is typically 1-5 GB in size")
    print("      Download may take time depending on your connection")
    print()


if __name__ == "__main__":
    main()
