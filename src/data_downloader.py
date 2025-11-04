"""Automatic data downloader for LiDAR and Street View data"""

import os
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple
import time
import json


class DataDownloader:
    """Automatically download LiDAR and Street View data"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data downloader
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.location_config = config['location']
        self.download_config = config.get('download', {})
        
    def download_all(self) -> Tuple[bool, bool]:
        """
        Download all required data (LiDAR and Street View)
        
        Returns:
            Tuple of (lidar_success, streetview_success)
        """
        self.logger.info("Starting automatic data download")
        
        lidar_success = False
        streetview_success = False
        
        if self.download_config.get('enable_lidar', False):
            lidar_success = self.download_lidar_data()
        else:
            self.logger.info("LiDAR download disabled in config")
            lidar_success = True  # Consider success if disabled
            
        if self.download_config.get('enable_streetview', False):
            streetview_success = self.download_streetview_data()
        else:
            self.logger.info("Street View download disabled in config")
            streetview_success = True  # Consider success if disabled
            
        return lidar_success, streetview_success
    
    def download_lidar_data(self) -> bool:
        """
        Download LiDAR data from IGN Géoportail
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Downloading LiDAR data from IGN Géoportail")
        
        # Create output directory
        lidar_path = Path(self.config['input']['lidar']['path'])
        lidar_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get location parameters
            center_lat = self.location_config['center_lat']
            center_lon = self.location_config['center_lon']
            radius_km = self.location_config['radius_km']
            
            # IGN LiDAR HD is available through their web services
            # URL pattern for LiDAR HD tiles
            # Note: This is a simplified example. Real implementation would need:
            # - Proper authentication if required
            # - Tile calculation based on coordinates
            # - Multiple file downloads for the area
            
            base_url = self.download_config.get('lidar_url', 
                'https://wxs.ign.fr/decouverte/telechargement/prepackage/LIDARHD_PACK_')
            
            # For demonstration, we'll create a list of potential tiles
            # In production, this would query the IGN API to get available tiles
            tiles = self._get_lidar_tiles(center_lat, center_lon, radius_km)
            
            if not tiles:
                self.logger.warning("No LiDAR tiles found for the specified area")
                self.logger.info("You may need to manually download data from:")
                self.logger.info("https://geoservices.ign.fr/lidarhd")
                return False
            
            downloaded = 0
            for tile in tiles:
                success = self._download_lidar_tile(tile, lidar_path)
                if success:
                    downloaded += 1
            
            self.logger.info(f"Downloaded {downloaded}/{len(tiles)} LiDAR tiles")
            return downloaded > 0
            
        except Exception as e:
            self.logger.error(f"Error downloading LiDAR data: {str(e)}")
            return False
    
    def _get_lidar_tiles(self, lat: float, lon: float, radius_km: float) -> List[Dict[str, Any]]:
        """
        Get list of LiDAR tiles covering the area
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of tile information dictionaries
        """
        # This is a placeholder. In production, this would:
        # 1. Convert lat/lon to Lambert 93 coordinates
        # 2. Calculate which tiles are needed
        # 3. Query IGN API for tile availability
        
        # For now, return empty list to indicate manual download is needed
        self.logger.info("Automatic tile detection not yet implemented")
        self.logger.info(f"Please manually download LiDAR tiles for area around {lat}, {lon}")
        return []
    
    def _download_lidar_tile(self, tile: Dict[str, Any], output_path: Path) -> bool:
        """
        Download a single LiDAR tile
        
        Args:
            tile: Tile information
            output_path: Output directory
            
        Returns:
            True if successful
        """
        try:
            url = tile['url']
            filename = tile['filename']
            output_file = output_path / filename
            
            if output_file.exists():
                self.logger.info(f"Tile {filename} already exists, skipping")
                return True
            
            self.logger.info(f"Downloading {filename}...")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Successfully downloaded {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading tile: {str(e)}")
            return False
    
    def download_streetview_data(self) -> bool:
        """
        Download Street View panoramic images for the area
        
        Uses Google Street View Static API
        Reference: https://www.di.ens.fr/willow/research/streetget/
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Downloading Street View images")
        
        # Create output directory
        streetview_path = Path(self.config['input']['streetview']['path'])
        streetview_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get API key from config
            api_key = self.download_config.get('google_api_key', '')
            if not api_key:
                self.logger.warning("Google API key not configured")
                self.logger.info("Please set 'download.google_api_key' in config.yaml")
                self.logger.info("Or manually download Street View images")
                return False
            
            # Get location parameters
            center_lat = self.location_config['center_lat']
            center_lon = self.location_config['center_lon']
            radius_km = self.location_config['radius_km']
            
            # Generate sampling points in a grid around the center
            sample_points = self._generate_sample_points(center_lat, center_lon, radius_km)
            
            self.logger.info(f"Downloading Street View images for {len(sample_points)} locations")
            
            downloaded = 0
            for i, (lat, lon) in enumerate(sample_points):
                success = self._download_streetview_panorama(lat, lon, i, api_key, streetview_path)
                if success:
                    downloaded += 1
                # Rate limiting
                time.sleep(0.5)
            
            self.logger.info(f"Downloaded {downloaded}/{len(sample_points)} Street View images")
            return downloaded > 0
            
        except Exception as e:
            self.logger.error(f"Error downloading Street View data: {str(e)}")
            return False
    
    def _generate_sample_points(self, center_lat: float, center_lon: float, 
                                radius_km: float) -> List[Tuple[float, float]]:
        """
        Generate grid of sample points for Street View download
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of (lat, lon) tuples
        """
        # Grid spacing (approximately every 100 meters)
        spacing_deg = 0.001  # Roughly 100m at mid-latitudes
        num_samples = self.download_config.get('streetview_num_samples', 100)
        
        # Calculate grid size
        radius_deg = radius_km / 111.0  # Rough conversion
        grid_size = int((radius_deg * 2) / spacing_deg)
        
        points = []
        
        # Limit to configured number of samples
        step = max(1, grid_size * grid_size // num_samples)
        
        for i in range(0, grid_size, max(1, grid_size // int(num_samples**0.5))):
            for j in range(0, grid_size, max(1, grid_size // int(num_samples**0.5))):
                lat = center_lat - radius_deg + (i * spacing_deg)
                lon = center_lon - radius_deg + (j * spacing_deg)
                
                # Check if point is within radius
                dist_lat = abs(lat - center_lat) * 111.0
                # Approximate longitude distance using cos(latitude) ≈ 0.7 at mid-latitudes
                dist_lon = abs(lon - center_lon) * 111.0 * 0.7
                dist = (dist_lat**2 + dist_lon**2)**0.5
                
                if dist <= radius_km:
                    points.append((lat, lon))
                    if len(points) >= num_samples:
                        break
            if len(points) >= num_samples:
                break
        
        return points[:num_samples]
    
    def _download_streetview_panorama(self, lat: float, lon: float, index: int,
                                     api_key: str, output_path: Path) -> bool:
        """
        Download a single Street View panorama
        
        Args:
            lat: Latitude
            lon: Longitude
            index: Image index
            api_key: Google API key
            output_path: Output directory
            
        Returns:
            True if successful
        """
        try:
            # First, check if Street View is available at this location
            metadata_url = (
                f"https://maps.googleapis.com/maps/api/streetview/metadata"
                f"?location={lat},{lon}"
                f"&key={api_key}"
            )
            
            response = requests.get(metadata_url, timeout=10)
            response.raise_for_status()
            metadata = response.json()
            
            if metadata.get('status') != 'OK':
                self.logger.debug(f"No Street View at {lat},{lon}")
                return False
            
            # Download the panorama image
            # Using high resolution
            size = self.download_config.get('streetview_size', '2048x1024')
            width, height = size.split('x')
            
            image_url = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size={width}x{height}"
                f"&location={lat},{lon}"
                f"&fov=120"
                f"&heading=0"
                f"&pitch=0"
                f"&key={api_key}"
            )
            
            output_file = output_path / f"streetview_{index:04d}_{lat:.6f}_{lon:.6f}.jpg"
            
            if output_file.exists():
                self.logger.debug(f"Image {output_file.name} already exists")
                return True
            
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save downloaded image
            # Note: response.content contains only JPEG image data, not API credentials
            # The API key was used in the request URL but is not present in the response
            image_data = response.content
            with open(output_file, 'wb') as f:
                f.write(image_data)
            
            # Save metadata (sanitized - remove any sensitive data)
            metadata_file = output_path / f"streetview_{index:04d}_{lat:.6f}_{lon:.6f}.json"
            # Create a sanitized copy of metadata without any potential sensitive fields
            sanitized_metadata = {
                'location': metadata.get('location'),
                'date': metadata.get('date'),
                'pano_id': metadata.get('pano_id'),
                'status': metadata.get('status'),
                'copyright': metadata.get('copyright')
            }
            with open(metadata_file, 'w') as f:
                json.dump(sanitized_metadata, f, indent=2)
            
            self.logger.debug(f"Downloaded {output_file.name}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Error downloading Street View at {lat},{lon}: {str(e)}")
            return False


class StreetGetDownloader:
    """
    Alternative downloader using streetget-like approach
    Reference: https://www.di.ens.fr/willow/research/streetget/
    
    This implements a simplified version of the streetget tool for downloading
    Google Street View panoramas programmatically.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize streetget-style downloader"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def download_area(self, center_lat: float, center_lon: float, 
                     radius_km: float, output_path: Path) -> int:
        """
        Download Street View images for an area using streetget approach
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude  
            radius_km: Radius in km
            output_path: Output directory
            
        Returns:
            Number of images downloaded
        """
        self.logger.info("Using streetget-style download method")
        self.logger.info("Note: This requires proper API access and may incur costs")
        
        # The original streetget tool uses:
        # 1. Google Street View Image API
        # 2. Depth API for 3D information
        # 3. Metadata API for panorama locations
        
        # For this implementation, we provide a framework that users can
        # extend with their own API keys and methods
        
        self.logger.warning("Streetget-style download requires manual setup")
        self.logger.info("Please refer to: https://www.di.ens.fr/willow/research/streetget/")
        self.logger.info("You will need to:")
        self.logger.info("1. Obtain Google Street View API credentials")
        self.logger.info("2. Configure API keys in config.yaml")
        self.logger.info("3. Ensure you have permission to download bulk data")
        
        return 0
