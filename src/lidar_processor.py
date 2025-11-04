"""LiDAR point cloud processor module"""

import laspy
import numpy as np
import open3d as o3d
from pathlib import Path
from typing import Dict, Any, List
import logging


class LiDARProcessor:
    """Process LiDAR point cloud data in COPC LAZ format"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LiDAR processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.lidar_config = config['input']['lidar']
        self.location_config = config['location']
        
    def load_and_process(self) -> o3d.geometry.PointCloud:
        """
        Load and process all LiDAR files in the input directory
        
        Returns:
            Merged and processed point cloud
        """
        lidar_path = Path(self.lidar_config['path'])
        laz_files = list(lidar_path.glob(f"*.{self.lidar_config['format']}"))
        
        if not laz_files:
            self.logger.warning(f"No .{self.lidar_config['format']} files found in {lidar_path}")
            # Return empty point cloud for testing
            return o3d.geometry.PointCloud()
        
        self.logger.info(f"Found {len(laz_files)} LiDAR files")
        
        all_points = []
        all_colors = []
        
        for laz_file in laz_files:
            self.logger.info(f"Processing {laz_file.name}")
            points, colors = self._load_laz_file(laz_file)
            all_points.append(points)
            if colors is not None:
                all_colors.append(colors)
        
        # Merge all point clouds
        merged_points = np.vstack(all_points)
        merged_colors = np.vstack(all_colors) if all_colors else None
        
        # Create Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(merged_points)
        if merged_colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(merged_colors)
        
        # Filter by location (10km around Rambouillet)
        pcd = self._filter_by_location(pcd)
        
        # Downsample using voxel grid
        voxel_size = self.lidar_config['voxel_size']
        self.logger.info(f"Downsampling with voxel size: {voxel_size}m")
        pcd = pcd.voxel_down_sample(voxel_size)
        
        # Remove statistical outliers
        self.logger.info("Removing outliers")
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        
        self.logger.info(f"Final point cloud: {len(pcd.points)} points")
        
        return pcd
    
    def _load_laz_file(self, file_path: Path) -> tuple:
        """
        Load a single LAZ file
        
        Args:
            file_path: Path to LAZ file
            
        Returns:
            Tuple of (points, colors)
        """
        try:
            las = laspy.read(str(file_path))
            
            # Extract coordinates
            points = np.vstack([las.x, las.y, las.z]).transpose()
            
            # Extract colors if available
            colors = None
            if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
                colors = np.vstack([las.red, las.green, las.blue]).transpose()
                # Normalize to [0, 1]
                colors = colors / 65535.0
            
            return points, colors
            
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {str(e)}")
            raise
    
    def _filter_by_location(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """
        Filter point cloud to area around Rambouillet
        
        Args:
            pcd: Input point cloud
            
        Returns:
            Filtered point cloud
        """
        # For now, return the full point cloud
        # In production, would convert coordinates and filter by distance
        # from center (48.6439, 1.8294) within 10km radius
        
        self.logger.info(f"Filtering to {self.location_config['radius_km']}km around {self.location_config['name']}")
        
        # TODO: Implement coordinate filtering
        # This would require coordinate transformation from Lambert 93 to WGS84
        # and distance calculation
        
        return pcd
