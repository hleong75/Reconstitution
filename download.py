#!/usr/bin/env python3
"""
Download utility for Reconstitution 3D pipeline
Helps users download data automatically without paid APIs
"""

import sys
import yaml
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def show_info():
    """Show information about data sources"""
    print("\n" + "="*70)
    print("  Reconstitution 3D - Data Download Information")
    print("="*70)
    
    print("\nThis tool downloads data from FREE public sources (no paid APIs):\n")
    
    print("1. LiDAR HD Data (from IGN Géoportail)")
    print("   - Source: France's National Geographic Institute")
    print("   - Coverage: France territory")
    print("   - Format: COPC LAZ (Cloud Optimized Point Cloud)")
    print("   - Resolution: High-density LiDAR (10+ points/m²)")
    print("   - Cost: FREE (public data)")
    print("   - Website: https://geoservices.ign.fr/lidarhd")
    
    print("\n2. Street View Images (from Mapillary)")
    print("   - Source: Mapillary community imagery")
    print("   - Coverage: Worldwide")
    print("   - Format: JPEG panoramic images")
    print("   - Resolution: Up to 2048x1024")
    print("   - Cost: FREE (requires free API token)")
    print("   - Website: https://www.mapillary.com/")
    print("   - Get API token: https://www.mapillary.com/developer")
    
    print("\n" + "="*70)
    print("  No Google APIs or paid services required!")
    print("="*70 + "\n")


def setup_mapillary():
    """Interactive setup for Mapillary token"""
    print("\n" + "="*70)
    print("  Mapillary Setup")
    print("="*70 + "\n")
    
    print("Mapillary provides free street-level imagery as an alternative to")
    print("Google Street View. To use it, you need a free API token.\n")
    
    print("Steps to get your token:")
    print("1. Visit: https://www.mapillary.com/developer")
    print("2. Sign up for a free account (or log in)")
    print("3. Create a new application")
    print("4. Copy your Client Token\n")
    
    token = input("Enter your Mapillary Client Token (or press Enter to skip): ").strip()
    
    if not token:
        print("\nNo token entered. You can add it later in config.yaml")
        print("under: download.mapillary_token")
        return False
    
    # Update config
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        if 'download' not in config:
            config['download'] = {}
        
        config['download']['mapillary_token'] = token
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print("\n✓ Token saved to config.yaml")
        return True
        
    except Exception as e:
        logger.error(f"Error saving token: {e}")
        return False


def download_now():
    """Download data now"""
    print("\n" + "="*70)
    print("  Downloading Data")
    print("="*70 + "\n")
    
    try:
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Import and run downloader
        from src.auto_downloader import AutoDownloader
        
        downloader = AutoDownloader(config)
        lidar_ok, streetview_ok = downloader.download_all()
        
        print("\n" + "="*70)
        if lidar_ok or streetview_ok:
            print("  Download completed!")
            print("  You can now run: python main.py")
        else:
            print("  Download had issues. See manual instructions above.")
            downloader.print_manual_instructions()
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Error during download: {e}")
        logger.info("\nTry manual download or check your configuration")


def test_download():
    """Test download configuration"""
    print("\n" + "="*70)
    print("  Testing Download Configuration")
    print("="*70 + "\n")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        download_config = config.get('download', {})
        
        print("Configuration:")
        print(f"  LiDAR download: {'✓ Enabled' if download_config.get('enable_lidar') else '✗ Disabled'}")
        print(f"  Street View download: {'✓ Enabled' if download_config.get('enable_streetview') else '✗ Disabled'}")
        
        mapillary_token = download_config.get('mapillary_token', '')
        if mapillary_token:
            print(f"  Mapillary token: ✓ Configured ({mapillary_token[:8]}...)")
        else:
            print("  Mapillary token: ✗ Not configured")
            print("    Run: python download.py setup-mapillary")
        
        print(f"\nLocation:")
        location = config.get('location', {})
        print(f"  City: {location.get('name')}")
        print(f"  Coordinates: {location.get('center_lat')}, {location.get('center_lon')}")
        print(f"  Radius: {location.get('radius_km')} km")
        
        print("\n✓ Configuration looks good!")
        
    except Exception as e:
        logger.error(f"Error reading configuration: {e}")


def show_manual_instructions():
    """Show manual download instructions"""
    print("\n" + "="*70)
    print("  Manual Download Instructions")
    print("="*70 + "\n")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        location = config.get('location', {})
        
        print("If automatic download doesn't work, download data manually:\n")
        
        print("1. LiDAR HD Data:")
        print(f"   a. Visit: https://geoservices.ign.fr/lidarhd")
        print(f"   b. Search for: {location.get('name')} ({location.get('center_lat')}, {location.get('center_lon')})")
        print(f"   c. Download .copc.laz files for your area")
        print(f"   d. Place files in: data/lidar/")
        
        print("\n2. Street View Images:")
        print("   Option A - Mapillary:")
        print("     a. Get free API token: https://www.mapillary.com/developer")
        print("     b. Run: python download.py setup-mapillary")
        print("     c. Run: python download.py now")
        
        print("\n   Option B - Manual collection:")
        print("     a. Take your own photos or find openly licensed images")
        print("     b. Save as JPG files")
        print("     c. Place in: data/streetview/")
        
    except Exception as e:
        logger.error(f"Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\nReconstitution 3D - Download Utility\n")
        print("Usage:")
        print("  python download.py info                 - Show data sources info")
        print("  python download.py setup-mapillary      - Setup Mapillary token")
        print("  python download.py test                 - Test configuration")
        print("  python download.py now                  - Download data now")
        print("  python download.py manual               - Show manual instructions")
        print("\nExample workflow:")
        print("  1. python download.py info")
        print("  2. python download.py setup-mapillary")
        print("  3. python download.py now")
        print("  4. python main.py --city Rambouillet --radius 10")
        print()
        return
    
    command = sys.argv[1].lower()
    
    if command == "info":
        show_info()
    elif command == "setup-mapillary":
        setup_mapillary()
    elif command == "test":
        test_download()
    elif command == "now":
        download_now()
    elif command == "manual":
        show_manual_instructions()
    else:
        logger.error(f"Unknown command: {command}")
        logger.info("Run 'python download.py' for help")


if __name__ == "__main__":
    main()
