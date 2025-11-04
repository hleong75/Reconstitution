"""AI-based segmentation module for point clouds"""

import numpy as np
import open3d as o3d
from typing import Dict, Any, List
import logging
import torch
import torch.nn as nn
from pathlib import Path


class PointNetSegmentation(nn.Module):
    """Simple PointNet-based segmentation network"""
    
    def __init__(self, num_classes=4):
        super(PointNetSegmentation, self).__init__()
        self.num_classes = num_classes
        
        # Feature extraction layers
        self.conv1 = nn.Conv1d(3, 64, 1)
        self.conv2 = nn.Conv1d(64, 128, 1)
        self.conv3 = nn.Conv1d(128, 1024, 1)
        
        # Segmentation layers
        self.conv4 = nn.Conv1d(1088, 512, 1)
        self.conv5 = nn.Conv1d(512, 256, 1)
        self.conv6 = nn.Conv1d(256, num_classes, 1)
        
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        self.bn5 = nn.BatchNorm1d(256)
        
        self.relu = nn.ReLU()
    
    def forward(self, x):
        """Forward pass"""
        n_pts = x.size(2)
        
        # Feature extraction
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.relu(self.bn3(self.conv3(x)))
        
        # Global feature
        global_feature = torch.max(x, 2, keepdim=True)[0]
        global_feature_expanded = global_feature.repeat(1, 1, n_pts)
        
        # Concatenate with point features
        x = torch.cat([x, global_feature_expanded], 1)
        
        # Segmentation head
        x = self.relu(self.bn4(self.conv4(x)))
        x = self.relu(self.bn5(self.conv5(x)))
        x = self.conv6(x)
        
        return x


class AISegmentation:
    """AI-based point cloud segmentation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI segmentation
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.seg_config = config['processing']['segmentation']
        
        # Store last predictions for extraction
        self._last_predictions = None
        self._last_point_cloud = None
        
        # Initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.info(f"Using device: {self.device}")
        
        num_classes = len(self.seg_config['classes'])
        self.model = PointNetSegmentation(num_classes=num_classes).to(self.device)
        
        # Load weights if available
        self._load_weights()
        
        self.model.eval()
    
    def _load_weights(self):
        """Load pre-trained weights if available"""
        weights_path = self.seg_config.get('weights_path')
        if weights_path and Path(weights_path).exists():
            self.logger.info(f"Loading weights from {weights_path}")
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        else:
            self.logger.warning("No pre-trained weights found, using random initialization")
    
    def segment(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """
        Segment point cloud into different classes
        Uses simple height-based segmentation as fallback when AI model fails
        
        Args:
            pcd: Input point cloud
            
        Returns:
            Point cloud with segmentation labels
        """
        if len(pcd.points) == 0:
            self.logger.warning("Empty point cloud, skipping segmentation")
            pcd.colors = o3d.utility.Vector3dVector(np.zeros((0, 3)))
            return pcd
        
        points = np.asarray(pcd.points)
        
        # Try AI-based segmentation first
        try:
            # Normalize points
            centroid = np.mean(points, axis=0)
            points_normalized = points - centroid
            max_dist = np.max(np.linalg.norm(points_normalized, axis=1))
            if max_dist > 0:
                points_normalized = points_normalized / max_dist
            
            # Prepare input for model
            points_tensor = torch.FloatTensor(points_normalized.T).unsqueeze(0).to(self.device)
            
            # Run segmentation
            with torch.no_grad():
                logits = self.model(points_tensor)
                predictions = torch.argmax(logits, dim=1).squeeze().cpu().numpy()
            
            self.logger.info("Using AI-based segmentation")
            
        except Exception as e:
            # Fallback to simple height-based segmentation
            self.logger.warning(f"AI segmentation failed: {str(e)}")
            self.logger.info("Using fallback height-based segmentation")
            predictions = self._simple_height_segmentation(points)
        
        # Color code by class
        colors = self._get_class_colors(predictions)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Store labels and point cloud for extraction methods
        self._last_predictions = predictions
        self._last_point_cloud = pcd
        
        self.logger.info(f"Segmented {len(points)} points into {len(self.seg_config['classes'])} classes")
        
        return pcd
    
    def _simple_height_segmentation(self, points: np.ndarray) -> np.ndarray:
        """
        Simple height-based segmentation fallback
        
        Args:
            points: Point cloud array (N, 3)
            
        Returns:
            Class labels for each point
        """
        z_values = points[:, 2]
        z_min = z_values.min()
        z_max = z_values.max()
        z_range = z_max - z_min
        
        labels = np.zeros(len(points), dtype=np.int32)
        
        # Ground: lowest 20% of points
        ground_threshold = z_min + 0.2 * z_range
        labels[z_values <= ground_threshold] = 0  # ground
        
        # Buildings: mid-range heights (20%-80%)
        building_threshold = z_min + 0.8 * z_range
        building_mask = (z_values > ground_threshold) & (z_values < building_threshold)
        labels[building_mask] = 1  # building
        
        # Vegetation/other: highest points
        labels[z_values >= building_threshold] = 2  # vegetation
        
        return labels
    
    def _get_class_colors(self, labels: np.ndarray) -> np.ndarray:
        """
        Get colors for each class
        
        Args:
            labels: Class labels
            
        Returns:
            RGB colors for each point
        """
        color_map = {
            0: [0.6, 0.4, 0.2],  # ground - brown
            1: [0.8, 0.2, 0.2],  # building - red
            2: [0.2, 0.8, 0.2],  # vegetation - green
            3: [0.5, 0.5, 0.5],  # other - gray
        }
        
        colors = np.array([color_map.get(label, [0.5, 0.5, 0.5]) for label in labels])
        return colors
    
    def extract_buildings(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """
        Extract building points from segmented cloud
        
        Args:
            pcd: Segmented point cloud
            
        Returns:
            Point cloud containing only buildings
        """
        if self._last_predictions is None:
            self.logger.warning("Point cloud not segmented, cannot extract buildings")
            return o3d.geometry.PointCloud()
        
        # Class 1 is buildings
        building_mask = self._last_predictions == 1
        
        building_pcd = pcd.select_by_index(np.where(building_mask)[0])
        
        self.logger.info(f"Extracted {len(building_pcd.points)} building points")
        
        return building_pcd
    
    def extract_ground(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """
        Extract ground points from segmented cloud
        
        Args:
            pcd: Segmented point cloud
            
        Returns:
            Point cloud containing only ground
        """
        if self._last_predictions is None:
            self.logger.warning("Point cloud not segmented, cannot extract ground")
            return o3d.geometry.PointCloud()
        
        # Class 0 is ground
        ground_mask = self._last_predictions == 0
        
        ground_pcd = pcd.select_by_index(np.where(ground_mask)[0])
        
        self.logger.info(f"Extracted {len(ground_pcd.points)} ground points")
        
        return ground_pcd
