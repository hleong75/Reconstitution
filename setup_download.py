#!/usr/bin/env python3
"""
Setup script for configuring automatic data download
Helps users configure API keys and download settings
"""

import yaml
import sys
from pathlib import Path


def setup_download_config():
    """Interactive setup for download configuration"""
    print("=" * 70)
    print("Reconstitution - Automatic Data Download Setup")
    print("=" * 70)
    print()
    
    # Load existing config
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("Error: config.yaml not found!")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'download' not in config:
        config['download'] = {}
    
    print("This script will help you configure automatic data download.")
    print()
    
    # LiDAR configuration
    print("1. LiDAR Data Download")
    print("-" * 70)
    print("LiDAR HD data from IGN Géoportail")
    print("Note: Automatic LiDAR download is currently limited.")
    print("For best results, manually download from:")
    print("https://geoservices.ign.fr/lidarhd")
    print()
    
    lidar_enable = input("Enable automatic LiDAR download attempt? (y/N): ").lower().strip()
    config['download']['enable_lidar'] = lidar_enable == 'y'
    
    print()
    
    # Street View configuration
    print("2. Google Street View Download")
    print("-" * 70)
    print("Download panoramic images using Google Street View Static API")
    print("Reference: https://www.di.ens.fr/willow/research/streetget/")
    print()
    print("Requirements:")
    print("  - Google Cloud Platform account")
    print("  - Street View Static API enabled")
    print("  - Valid API key with billing enabled")
    print()
    print("Get your API key from:")
    print("https://console.cloud.google.com/apis/credentials")
    print()
    
    sv_enable = input("Enable Street View download? (y/N): ").lower().strip()
    config['download']['enable_streetview'] = sv_enable == 'y'
    
    if sv_enable == 'y':
        print()
        api_key = input("Enter your Google Maps API key (or press Enter to skip): ").strip()
        if api_key:
            config['download']['google_api_key'] = api_key
            print("✓ API key configured")
        else:
            config['download']['google_api_key'] = ""
            print("! API key not set - you can add it later in config.yaml")
        
        print()
        num_samples = input("Number of Street View images to download (default: 50): ").strip()
        if num_samples and num_samples.isdigit():
            config['download']['streetview_num_samples'] = int(num_samples)
        else:
            config['download']['streetview_num_samples'] = 50
        
        print()
        size = input("Image resolution (default: 2048x1024): ").strip()
        if size:
            config['download']['streetview_size'] = size
        else:
            config['download']['streetview_size'] = "2048x1024"
    
    # Save configuration
    print()
    print("Saving configuration...")
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("✓ Configuration saved to config.yaml")
    print()
    
    # Show summary
    print("=" * 70)
    print("Configuration Summary")
    print("=" * 70)
    print(f"LiDAR auto-download: {'Enabled' if config['download']['enable_lidar'] else 'Disabled'}")
    print(f"Street View auto-download: {'Enabled' if config['download']['enable_streetview'] else 'Disabled'}")
    
    if config['download']['enable_streetview']:
        has_key = bool(config['download'].get('google_api_key'))
        print(f"  API Key: {'Configured' if has_key else 'NOT CONFIGURED'}")
        print(f"  Number of images: {config['download'].get('streetview_num_samples', 50)}")
        print(f"  Image size: {config['download'].get('streetview_size', '2048x1024')}")
    
    print("=" * 70)
    print()
    
    # Next steps
    print("Next Steps:")
    print()
    
    if not config['download']['enable_lidar'] and not config['download']['enable_streetview']:
        print("1. Manually download LiDAR data from:")
        print("   https://geoservices.ign.fr/lidarhd")
        print("   Place .copc.laz files in: data/lidar/")
        print()
        print("2. Manually download or capture Street View images")
        print("   Place images in: data/streetview/")
        print()
    else:
        if config['download']['enable_streetview'] and not config['download'].get('google_api_key'):
            print("! Add your Google Maps API key to config.yaml before running")
            print()
    
    print("3. Run the pipeline:")
    print("   python main.py")
    print()
    
    return True


def show_download_info():
    """Show information about data download options"""
    print("=" * 70)
    print("Data Download Options")
    print("=" * 70)
    print()
    
    print("Option 1: Automatic Download (Recommended for Street View)")
    print("-" * 70)
    print("Configure automatic download with:")
    print("  python setup_download.py config")
    print()
    
    print("Option 2: Manual Download")
    print("-" * 70)
    print()
    print("LiDAR Data:")
    print("  1. Visit: https://geoservices.ign.fr/lidarhd")
    print("  2. Select your area of interest (Rambouillet region)")
    print("  3. Download .copc.laz files")
    print("  4. Place files in: data/lidar/")
    print()
    
    print("Street View Images:")
    print("  1. Use tools like:")
    print("     - streetget: https://www.di.ens.fr/willow/research/streetget/")
    print("     - Google Street View Downloader")
    print("     - Manual screenshots from Google Maps")
    print("  2. Place images in: data/streetview/")
    print()
    
    print("Option 3: Demo Data (For Testing)")
    print("-" * 70)
    print("Create synthetic demo data:")
    print("  python demo.py create")
    print()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'config':
            return 0 if setup_download_config() else 1
        elif sys.argv[1] == 'info':
            show_download_info()
            return 0
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print()
    
    # Default: show usage
    print("Reconstitution - Data Download Setup")
    print()
    print("Usage:")
    print("  python setup_download.py config  - Configure automatic download")
    print("  python setup_download.py info    - Show download information")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
