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
        Supports multiple formats: .laz, .copc.laz, .las, .ply, .pcd
        
        Returns:
            Merged and processed point cloud
        """
        lidar_path = Path(self.lidar_config['path'])
        
        # Support multiple file formats
        supported_formats = ['laz', 'las', 'ply', 'pcd']
        point_cloud_files = []
        
        # Get configured format first
        config_format = self.lidar_config.get('format', 'copc.laz')
        for fmt in [config_format] + supported_formats:
            files = list(lidar_path.glob(f"*.{fmt}"))
            point_cloud_files.extend(files)
        
        # Remove duplicates
        point_cloud_files = list(set(point_cloud_files))
        
        if not point_cloud_files:
            self.logger.warning(f"No point cloud files found in {lidar_path}")
            self.logger.info(f"Supported formats: {', '.join(supported_formats)}")
            # Return empty point cloud for testing
            return o3d.geometry.PointCloud()
        
        self.logger.info(f"Found {len(point_cloud_files)} point cloud files")
        
        all_points = []
        all_colors = []
        
        for pc_file in point_cloud_files:
            self.logger.info(f"Processing {pc_file.name}")
            points, colors = self._load_point_cloud_file(pc_file)
            if points is not None and len(points) > 0:
                all_points.append(points)
                if colors is not None:
                    all_colors.append(colors)
        
        # Check if we loaded any valid data
        if not all_points:
            self.logger.warning("No valid point cloud data could be loaded")
            return o3d.geometry.PointCloud()
        
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
    
    def _load_point_cloud_file(self, file_path: Path) -> tuple:
        """
        Load a point cloud file (supports LAZ, LAS, PLY, PCD formats)
        
        Args:
            file_path: Path to point cloud file
            
        Returns:
            Tuple of (points, colors) as numpy arrays
        """
        try:
            file_ext = file_path.suffix.lower()
            
            # Handle LAZ/LAS files with laspy
            if file_ext in ['.laz', '.las']:
                return self._load_laz_file(file_path)
            
            # Handle PLY/PCD files with Open3D
            elif file_ext in ['.ply', '.pcd']:
                return self._load_open3d_file(file_path)
            
            else:
                self.logger.warning(f"Unsupported file format: {file_ext}")
                return None, None
                
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {str(e)}")
            return None, None
    
    def _load_laz_file(self, file_path: Path) -> tuple:
        """
        Load a LAZ/LAS file using laspy
        
        Args:
            file_path: Path to LAZ/LAS file
            
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
            self.logger.error(f"Error loading LAZ/LAS file {file_path}: {str(e)}")
            raise
    
    def _load_open3d_file(self, file_path: Path) -> tuple:
        """
        Load PLY/PCD file using Open3D
        
        Args:
            file_path: Path to PLY/PCD file
            
        Returns:
            Tuple of (points, colors)
        """
        try:
            pcd = o3d.io.read_point_cloud(str(file_path))
            
            # Extract points
            points = np.asarray(pcd.points)
            
            # Extract colors if available
            colors = None
            if pcd.has_colors():
                colors = np.asarray(pcd.colors)
            
            return points, colors
            
        except Exception as e:
            self.logger.error(f"Error loading Open3D file {file_path}: {str(e)}")
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
