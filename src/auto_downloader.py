"""
Automatic data downloader for LiDAR and Street View imagery
WITHOUT using paid APIs - uses public data sources only
"""

import os
import sys
import logging
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import time
import json
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class IGNLidarDownloader:
    """
    Download LiDAR HD data from IGN Géoportail
    Uses publicly accessible download links without API authentication
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize IGN LiDAR downloader"""
        self.config = config
        self.location = config['location']
        
    def download(self, output_dir: Path) -> bool:
        """
        Download LiDAR data for configured location
        
        Args:
            output_dir: Directory to save downloaded files
            
        Returns:
            True if successful
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        lat = self.location['center_lat']
        lon = self.location['center_lon']
        
        logger.info(f"Downloading IGN LiDAR HD data for {lat}, {lon}")
        
        # Convert WGS84 to Lambert 93 to find tile names
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
            x_lambert, y_lambert = transformer.transform(lon, lat)
            
            # IGN tiles are 1km x 1km, named by lower-left corner in km
            tile_x = int(x_lambert / 1000)
            tile_y = int(y_lambert / 1000)
            
            logger.info(f"Lambert 93 coordinates: X={x_lambert:.2f}, Y={y_lambert:.2f}")
            logger.info(f"Tile coordinates: X={tile_x}, Y={tile_y}")
            
        except ImportError:
            logger.warning("pyproj not installed, using approximate coordinates")
            # Rough approximation for France
            tile_x = 600 + int((lon - 2.5) * 100)
            tile_y = 6800 + int((lat - 46.5) * 110)
        
        # Try to download tiles in the area
        radius_km = self.location.get('radius_km', 10)
        tiles_downloaded = 0
        
        # Calculate number of tiles needed
        tiles_per_side = max(1, int(radius_km / 1.0) + 1)
        
        for dx in range(-tiles_per_side, tiles_per_side + 1):
            for dy in range(-tiles_per_side, tiles_per_side + 1):
                tx = tile_x + dx
                ty = tile_y + dy
                
                success = self._download_tile(tx, ty, output_dir)
                if success:
                    tiles_downloaded += 1
                    
                # Don't hammer the server
                time.sleep(1)
                
                # Limit downloads for demo
                if tiles_downloaded >= 5:
                    logger.info("Downloaded 5 tiles, stopping (adjust if needed)")
                    break
            if tiles_downloaded >= 5:
                break
        
        logger.info(f"Downloaded {tiles_downloaded} LiDAR tiles")
        return tiles_downloaded > 0
    
    def _download_tile(self, x: int, y: int, output_dir: Path) -> bool:
        """
        Download a single LiDAR tile
        
        IGN provides public access to LiDAR HD data through their download service
        The data is organized by department and tile coordinates
        """
        # IGN LiDAR HD file naming pattern
        # Example: LHD_FXX_0600_6830_PTS_C_LAMB93_IGN69.copc.laz
        
        # Try different possible URLs and formats
        possible_urls = [
            # Public LIDAR HD download service (if available)
            f"https://download.ign.fr/pub/LIDARHD/LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz",
            # Alternative URL patterns
            f"https://storage.sbg.cloud.ovh.net/v1/AUTH_63234f509b4b4b0488a9f2b6dfa5aea5/IGNF/LIDAR/LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz",
        ]
        
        filename = f"LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz"
        output_file = output_dir / filename
        
        # Skip if already downloaded
        if output_file.exists():
            logger.info(f"Tile {filename} already exists")
            return True
        
        for url in possible_urls:
            try:
                logger.info(f"Trying to download from {url[:50]}...")
                response = requests.head(url, timeout=10)
                
                if response.status_code == 200:
                    # File exists, download it
                    logger.info(f"Downloading {filename}...")
                    response = requests.get(url, stream=True, timeout=300)
                    response.raise_for_status()
                    
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                    
                    logger.info(f"Successfully downloaded {filename}")
                    return True
                    
            except Exception as e:
                logger.debug(f"Failed to download from {url}: {e}")
                continue
        
        logger.warning(f"Could not download tile {x:04d}_{y:04d}")
        return False


class MapillaryDownloader:
    """
    Download street-level imagery from Mapillary (free, open-source alternative to Google Street View)
    Mapillary provides free API access for non-commercial use
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Mapillary downloader"""
        self.config = config
        self.location = config['location']
        # Mapillary client token (public, can be used for non-commercial purposes)
        # Users should get their own from https://www.mapillary.com/developer
        self.client_token = config.get('download', {}).get('mapillary_token', '')
        
    def download(self, output_dir: Path) -> bool:
        """
        Download street view images from Mapillary
        
        Args:
            output_dir: Directory to save images
            
        Returns:
            True if successful
        """
        if not self.client_token:
            logger.warning("No Mapillary token configured")
            logger.info("Get a free token at: https://www.mapillary.com/developer")
            logger.info("Mapillary provides free access to street-level imagery")
            return False
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        lat = self.location['center_lat']
        lon = self.location['center_lon']
        radius_m = self.location.get('radius_km', 10) * 1000
        
        logger.info(f"Downloading Mapillary images for {lat}, {lon}")
        
        # Search for images in the area
        images_info = self._search_images(lat, lon, radius_m)
        
        if not images_info:
            logger.warning("No Mapillary images found in this area")
            return False
        
        # Download images
        downloaded = 0
        max_images = self.config.get('download', {}).get('max_images', 50)
        
        for i, image_info in enumerate(images_info[:max_images]):
            success = self._download_image(image_info, output_dir, i)
            if success:
                downloaded += 1
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Downloaded {downloaded} Mapillary images")
        return downloaded > 0
    
    def _search_images(self, lat: float, lon: float, radius_m: float) -> List[Dict]:
        """Search for images in area using Mapillary API v4"""
        try:
            # Mapillary API v4 endpoint
            base_url = "https://graph.mapillary.com/images"
            
            params = {
                'access_token': self.client_token,
                'fields': 'id,thumb_2048_url,geometry,compass_angle',
                'bbox': f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",
                'limit': 100
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error searching Mapillary images: {e}")
            return []
    
    def _download_image(self, image_info: Dict, output_dir: Path, index: int) -> bool:
        """Download a single image"""
        try:
            image_id = image_info['id']
            thumb_url = image_info.get('thumb_2048_url')
            
            if not thumb_url:
                return False
            
            # Get geometry info
            geometry = image_info.get('geometry', {})
            coords = geometry.get('coordinates', [0, 0])
            
            filename = f"mapillary_{index:04d}_{coords[1]:.6f}_{coords[0]:.6f}.jpg"
            output_file = output_dir / filename
            
            if output_file.exists():
                return True
            
            response = requests.get(thumb_url, timeout=30)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            # Save metadata
            metadata = {
                'id': image_id,
                'lat': coords[1],
                'lon': coords[0],
                'compass_angle': image_info.get('compass_angle'),
            }
            
            metadata_file = output_dir / f"mapillary_{index:04d}_{coords[1]:.6f}_{coords[0]:.6f}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Downloaded {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading image {image_info.get('id')}: {e}")
            return False


class AutoDownloader:
    """
    Main automatic downloader - coordinates LiDAR and Street View downloads
    WITHOUT using paid Google APIs
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize auto downloader"""
        self.config = config
        self.lidar_downloader = IGNLidarDownloader(config)
        self.mapillary_downloader = MapillaryDownloader(config)
    
    def download_all(self) -> Tuple[bool, bool]:
        """
        Download all required data
        
        Returns:
            Tuple of (lidar_success, streetview_success)
        """
        logger.info("=== Starting Automatic Data Download ===")
        logger.info("Using FREE public data sources (no paid APIs)")
        
        lidar_success = False
        streetview_success = False
        
        # Download LiDAR data from IGN
        download_config = self.config.get('download', {})
        
        if download_config.get('enable_lidar', True):
            logger.info("\n--- Downloading LiDAR data from IGN ---")
            lidar_dir = Path(self.config['input']['lidar']['path'])
            lidar_success = self.lidar_downloader.download(lidar_dir)
        else:
            logger.info("LiDAR download disabled in config")
            lidar_success = True
        
        # Download Street View images from Mapillary
        if download_config.get('enable_streetview', True):
            logger.info("\n--- Downloading Street View images from Mapillary ---")
            streetview_dir = Path(self.config['input']['streetview']['path'])
            streetview_success = self.mapillary_downloader.download(streetview_dir)
        else:
            logger.info("Street View download disabled in config")
            streetview_success = True
        
        logger.info("\n=== Download Summary ===")
        logger.info(f"LiDAR: {'✓ Success' if lidar_success else '✗ Failed'}")
        logger.info(f"Street View: {'✓ Success' if streetview_success else '✗ Failed'}")
        
        return lidar_success, streetview_success
    
    def print_manual_instructions(self):
        """Print instructions for manual download if automatic fails"""
        logger.info("\n=== Manual Download Instructions ===")
        logger.info("\nIf automatic download fails, you can manually download data:")
        
        logger.info("\n1. LiDAR HD Data:")
        logger.info("   Visit: https://geoservices.ign.fr/lidarhd")
        logger.info(f"   Location: {self.config['location']['name']}")
        logger.info(f"   Coordinates: {self.config['location']['center_lat']}, {self.config['location']['center_lon']}")
        logger.info(f"   Place .copc.laz files in: {self.config['input']['lidar']['path']}")
        
        logger.info("\n2. Street View Images:")
        logger.info("   Option A - Mapillary (Free):")
        logger.info("     1. Get API token: https://www.mapillary.com/developer")
        logger.info("     2. Add to config.yaml: download.mapillary_token")
        logger.info("   Option B - Manual Collection:")
        logger.info(f"     Place JPG images in: {self.config['input']['streetview']['path']}")
