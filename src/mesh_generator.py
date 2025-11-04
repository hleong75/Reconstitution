"""3D Mesh generation module"""

import numpy as np
import open3d as o3d
from typing import Dict, Any
import logging


class MeshGenerator:
    """Generate 3D meshes from point clouds"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mesh generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mesh_config = config['mesh_generation']
    
    def generate(self, buildings: o3d.geometry.PointCloud, 
                 ground: o3d.geometry.PointCloud) -> o3d.geometry.TriangleMesh:
        """
        Generate 3D mesh from building and ground point clouds
        
        Args:
            buildings: Building point cloud
            ground: Ground point cloud
            
        Returns:
            Combined triangle mesh
        """
        self.logger.info("Generating 3D mesh")
        
        # Combine point clouds
        combined_pcd = buildings + ground
        
        if len(combined_pcd.points) == 0:
            self.logger.warning("Empty point cloud, returning empty mesh")
            return o3d.geometry.TriangleMesh()
        
        # Estimate normals
        self.logger.info("Estimating normals")
        combined_pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        combined_pcd.orient_normals_consistent_tangent_plane(100)
        
        # Generate mesh based on configured method
        method = self.mesh_config['method']
        
        if method == 'poisson':
            mesh = self._poisson_reconstruction(combined_pcd)
        elif method == 'ball_pivoting':
            mesh = self._ball_pivoting(combined_pcd)
        elif method == 'alpha_shape':
            mesh = self._alpha_shape(combined_pcd)
        else:
            self.logger.warning(f"Unknown method {method}, using Poisson")
            mesh = self._poisson_reconstruction(combined_pcd)
        
        # Simplify mesh
        mesh = self._simplify_mesh(mesh)
        
        # Clean mesh
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        
        self.logger.info(f"Generated mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
        
        return mesh
    
    def _poisson_reconstruction(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.TriangleMesh:
        """
        Poisson surface reconstruction
        
        Args:
            pcd: Input point cloud with normals
            
        Returns:
            Reconstructed mesh
        """
        self.logger.info("Running Poisson reconstruction")
        
        depth = self.mesh_config['poisson_depth']
        scale = self.mesh_config['poisson_scale']
        
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=depth, scale=scale
        )
        
        # Remove low density vertices
        densities = np.asarray(densities)
        vertices_to_remove = densities < np.quantile(densities, 0.01)
        mesh.remove_vertices_by_mask(vertices_to_remove)
        
        return mesh
    
    def _ball_pivoting(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.TriangleMesh:
        """
        Ball pivoting algorithm
        
        Args:
            pcd: Input point cloud with normals
            
        Returns:
            Reconstructed mesh
        """
        self.logger.info("Running Ball Pivoting algorithm")
        
        # Estimate radii
        distances = pcd.compute_nearest_neighbor_distance()
        avg_dist = np.mean(distances)
        radii = [avg_dist, avg_dist * 2, avg_dist * 4]
        
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
            pcd, o3d.utility.DoubleVector(radii)
        )
        
        return mesh
    
    def _alpha_shape(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.TriangleMesh:
        """
        Alpha shape algorithm
        
        Args:
            pcd: Input point cloud
            
        Returns:
            Reconstructed mesh
        """
        self.logger.info("Running Alpha Shape algorithm")
        
        # Calculate appropriate alpha value
        distances = pcd.compute_nearest_neighbor_distance()
        avg_dist = np.mean(distances)
        alpha = avg_dist * 2
        
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
        
        return mesh
    
    def _simplify_mesh(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """
        Simplify mesh to reduce polygon count
        
        Args:
            mesh: Input mesh
            
        Returns:
            Simplified mesh
        """
        ratio = self.mesh_config['simplification_ratio']
        target_triangles = int(len(mesh.triangles) * ratio)
        
        self.logger.info(f"Simplifying mesh to {target_triangles} triangles")
        
        simplified_mesh = mesh.simplify_quadric_decimation(target_triangles)
        
        return simplified_mesh
