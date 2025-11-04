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

# Configuration constants
IGN_TILE_SIZE_KM = 1.0  # IGN LiDAR tiles are 1km x 1km
TILE_SIZE_METERS = 1000  # Tile size in meters for coordinate conversion
TILE_GRID_PADDING = 1  # Additional tiles to check beyond calculated radius
MAX_FAILED_ATTEMPTS = 10  # Stop searching after this many consecutive failures
ATTEMPT_MULTIPLIER = 3  # Try this many times the desired tile count
REQUEST_DELAY_SECONDS = 0.5  # Delay between requests to avoid hammering server

# Approximate coordinate conversion constants (for fallback when pyproj unavailable)
# These are rough approximations for France only and should not be used for precise work
# Based on approximate center of France (lon ~2.5°E, lat ~46.5°N)
LAMBERT93_APPROX_TILE_X_OFFSET = 600  # Approximate X tile offset
LAMBERT93_APPROX_TILE_Y_OFFSET = 6800  # Approximate Y tile offset
LAMBERT93_APPROX_LON_REF = 2.5  # Reference longitude for approximation (degrees)
LAMBERT93_APPROX_LAT_REF = 46.5  # Reference latitude for approximation (degrees)
LAMBERT93_APPROX_LON_SCALE = 100  # Tile offset per degree longitude (rough)
LAMBERT93_APPROX_LAT_SCALE = 110  # Tile offset per degree latitude (rough)


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
        
        logger.info(f"Attempting to download IGN LiDAR HD data for {lat}, {lon}")
        
        # Convert WGS84 to Lambert 93 to find tile names
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
            x_lambert, y_lambert = transformer.transform(lon, lat)
            
            # IGN tiles are 1km x 1km, named by lower-left corner in km
            tile_x = int(x_lambert / TILE_SIZE_METERS)
            tile_y = int(y_lambert / TILE_SIZE_METERS)
            
            logger.info(f"Lambert 93 coordinates: X={x_lambert:.2f}, Y={y_lambert:.2f}")
            logger.info(f"Tile coordinates: X={tile_x}, Y={tile_y}")
            
        except ImportError:
            logger.warning("pyproj not installed, using approximate coordinates")
            logger.warning("Install pyproj for accurate coordinate conversion: pip install pyproj")
            # Rough approximation for France (NOT accurate for precise work)
            tile_x = LAMBERT93_APPROX_TILE_X_OFFSET + int((lon - LAMBERT93_APPROX_LON_REF) * LAMBERT93_APPROX_LON_SCALE)
            tile_y = LAMBERT93_APPROX_TILE_Y_OFFSET + int((lat - LAMBERT93_APPROX_LAT_REF) * LAMBERT93_APPROX_LAT_SCALE)
        except Exception as e:
            logger.error(f"Error converting coordinates: {e}")
            logger.warning("Using approximate coordinates")
            tile_x = LAMBERT93_APPROX_TILE_X_OFFSET + int((lon - LAMBERT93_APPROX_LON_REF) * LAMBERT93_APPROX_LON_SCALE)
            tile_y = LAMBERT93_APPROX_TILE_Y_OFFSET + int((lat - LAMBERT93_APPROX_LAT_REF) * LAMBERT93_APPROX_LAT_SCALE)
        
        # Try to download tiles in the area
        radius_km = self.location.get('radius_km', 10)
        tiles_downloaded = 0
        tiles_attempted = 0
        
        # Calculate number of tiles needed
        # Get max tiles from config, default to 5 for safety
        max_tiles = self.config.get('download', {}).get('max_lidar_tiles', 5)
        tiles_per_side = min(max_tiles, max(1, int(radius_km / IGN_TILE_SIZE_KM)))
        
        logger.info(f"Searching for LiDAR tiles in {radius_km}km radius (max {max_tiles} tiles)...")
        
        # Try tiles in a spiral pattern starting from center
        # This is more efficient than a full grid
        tiles_to_try = []
        for dx in range(-tiles_per_side, tiles_per_side + 1):
            for dy in range(-tiles_per_side, tiles_per_side + 1):
                # Calculate distance from center
                dist = (dx*dx + dy*dy) ** 0.5
                tiles_to_try.append((dist, dx, dy))
        
        # Sort by distance so we try closest tiles first
        tiles_to_try.sort()
        
        # Limit number of attempts to avoid excessive waiting
        max_attempts = min(max_tiles * ATTEMPT_MULTIPLIER, len(tiles_to_try))
        
        for dist, dx, dy in tiles_to_try[:max_attempts]:
            tx = tile_x + dx
            ty = tile_y + dy
            
            tiles_attempted += 1
            success = self._download_tile(tx, ty, output_dir)
            if success:
                tiles_downloaded += 1
                logger.info(f"Progress: {tiles_downloaded}/{max_tiles} tiles downloaded")
                
            # Small delay to avoid hammering the server
            if tiles_attempted < max_attempts:
                time.sleep(REQUEST_DELAY_SECONDS)
            
            # Stop if we have enough tiles
            if tiles_downloaded >= max_tiles:
                logger.info(f"✓ Downloaded {max_tiles} tiles (max configured)")
                break
            
            # Early exit if many consecutive failures
            if tiles_attempted >= MAX_FAILED_ATTEMPTS and tiles_downloaded == 0:
                logger.warning(f"No tiles found after {tiles_attempted} attempts, stopping search")
                break
        
        if tiles_downloaded > 0:
            logger.info(f"✓ Successfully downloaded {tiles_downloaded} LiDAR tile(s)")
            return True
        else:
            logger.warning("✗ Could not download any LiDAR tiles automatically")
            logger.warning(f"Attempted {tiles_attempted} tile locations but none were accessible")
            logger.warning("")
            logger.warning("This may be due to:")
            logger.warning("  1. Network restrictions or firewall blocking IGN servers")
            logger.warning("  2. IGN API changes or service unavailability")
            logger.warning("  3. Tiles not available for this specific location")
            logger.warning("  4. Authentication required for IGN data access")
            logger.warning("")
            logger.warning("MANUAL DOWNLOAD RECOMMENDED:")
            logger.warning(f"  1. Visit: https://geoservices.ign.fr/lidarhd")
            logger.warning(f"  2. Search for location: {self.location.get('name', 'your area')}")
            logger.warning(f"  3. Coordinates: {lat}, {lon}")
            logger.warning(f"  4. Download .copc.laz files covering your area")
            logger.warning(f"  5. Place files in: {output_dir}")
            logger.warning("")
            logger.warning("Alternative: Use IGN Geoplateforme at https://data.geopf.fr/")
            return False
    
    def _download_tile(self, x: int, y: int, output_dir: Path) -> bool:
        """
        Download a single LiDAR tile
        
        IGN provides public access to LiDAR HD data through their download service
        The data is organized by department and tile coordinates
        
        Note: As of 2024, IGN data is available through:
        - https://geoservices.ign.fr/lidarhd (web portal - manual download)
        - https://data.geopf.fr/ (new platform with API access)
        """
        # IGN LiDAR HD file naming pattern
        # Example: LHD_FXX_0600_6830_PTS_C_LAMB93_IGN69.copc.laz
        
        # Try different possible URLs and formats
        # Note: These URLs may require authentication or may not be publicly accessible
        possible_urls = [
            # New IGN Geoplateforme (as of 2024)
            f"https://data.geopf.fr/telechargement/download/LIDARHD/LIDARHD_1-0_LAZ_{x:04d}_{y:04d}/LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz",
            # Legacy public LIDAR HD download service
            f"https://download.ign.fr/pub/LIDARHD/LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz",
            # Alternative cloud storage
            f"https://storage.gra.cloud.ovh.net/v1/AUTH_63234f509b4b4b0488a9f2b6dfa5aea5/IGNF/LIDARHD_1-0_LAZ_{x:04d}_{y:04d}/LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz",
        ]
        
        filename = f"LHD_FXX_{x:04d}_{y:04d}_PTS_C_LAMB93_IGN69.copc.laz"
        output_file = output_dir / filename
        
        # Skip if already downloaded
        if output_file.exists():
            logger.info(f"Tile {filename} already exists")
            return True
        
        for i, url in enumerate(possible_urls):
            try:
                logger.debug(f"Attempting URL {i+1}/{len(possible_urls)}: {url[:80]}...")
                response = requests.head(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    # File exists, download it
                    logger.info(f"Downloading {filename} from source {i+1}...")
                    response = requests.get(url, stream=True, timeout=300)
                    response.raise_for_status()
                    
                    # Download with progress indication
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"Download progress: {progress:.1f}%")
                    
                    logger.info(f"Successfully downloaded {filename} ({downloaded / (1024*1024):.1f} MB)")
                    return True
                elif response.status_code == 404:
                    logger.debug(f"Tile not found at URL {i+1} (404)")
                else:
                    logger.debug(f"URL {i+1} returned status {response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                logger.debug(f"Connection error for URL {i+1}: Network unreachable or DNS resolution failed")
            except requests.exceptions.Timeout as e:
                logger.debug(f"Timeout for URL {i+1}: Request took too long")
            except Exception as e:
                logger.debug(f"Failed to download from URL {i+1}: {type(e).__name__}: {str(e)[:100]}")
                continue
        
        logger.debug(f"Could not download tile {x:04d}_{y:04d} from any source")
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
        logger.info("\n" + "="*70)
        logger.info("=== Manual Download Instructions ===")
        logger.info("="*70)
        logger.info("\nAutomatic download failed. Please download data manually:")
        
        logger.info("\n1. LiDAR HD Data (IGN - France):")
        logger.info("   Option A - IGN Geoservices (Recommended):")
        logger.info("     a. Visit: https://geoservices.ign.fr/lidarhd")
        logger.info(f"     b. Search for: {self.config['location']['name']}")
        logger.info(f"     c. Coordinates: {self.config['location']['center_lat']}, {self.config['location']['center_lon']}")
        logger.info("     d. Download .copc.laz or .laz files for your area")
        logger.info(f"     e. Place files in: {self.config['input']['lidar']['path']}")
        logger.info("")
        logger.info("   Option B - IGN Geoplateforme (New Platform):")
        logger.info("     a. Visit: https://data.geopf.fr/")
        logger.info("     b. Browse LIDARHD dataset")
        logger.info("     c. Select tiles covering your area")
        logger.info(f"     d. Place downloaded files in: {self.config['input']['lidar']['path']}")
        logger.info("")
        logger.info("   Note: IGN LiDAR HD covers France territory with high-density")
        logger.info("         point clouds (10+ points/m²). Files are typically 1-5 GB per tile.")
        
        logger.info("\n2. Street View Images (Mapillary - Worldwide):")
        logger.info("   Option A - Mapillary (Free API):")
        logger.info("     1. Get free API token: https://www.mapillary.com/developer")
        logger.info("     2. Add to config.yaml: download.mapillary_token: 'YOUR_TOKEN'")
        logger.info("     3. Run: python download.py now")
        logger.info("")
        logger.info("   Option B - Manual Collection:")
        logger.info("     1. Take your own photos or find openly licensed images")
        logger.info("     2. Save as JPG files")
        logger.info(f"     3. Place in: {self.config['input']['streetview']['path']}")
        logger.info("")
        logger.info("="*70 + "\n")
