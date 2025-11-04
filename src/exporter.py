"""3D model exporter module"""

import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path
from typing import Dict, Any
import logging


class ModelExporter:
    """Export 3D models to various formats"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize model exporter
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.output_config = config['output']
    
    def export_3ds(self, mesh: o3d.geometry.TriangleMesh) -> str:
        """
        Export mesh to .3ds format for Blender/3ds Max
        
        Args:
            mesh: Input mesh
            
        Returns:
            Path to exported file
        """
        self.logger.info("Exporting to .3ds format")
        
        output_path = Path(self.output_config['path'])
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = self.output_config['filename']
        output_file = output_path / f"{filename}.3ds"
        
        # Convert Open3D mesh to trimesh
        vertices = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)
        
        if len(vertices) == 0 or len(triangles) == 0:
            self.logger.warning("Empty mesh, creating placeholder")
            # Create a simple cube as placeholder
            vertices = np.array([
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
            ])
            triangles = np.array([
                [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
                [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
                [0, 3, 7], [0, 7, 4], [1, 5, 6], [1, 6, 2]
            ])
        
        # Get vertex colors if available
        vertex_colors = None
        if mesh.has_vertex_colors():
            vertex_colors = np.asarray(mesh.vertex_colors)
        
        # Create trimesh object
        tm = trimesh.Trimesh(
            vertices=vertices,
            faces=triangles,
            vertex_colors=vertex_colors
        )
        
        # Export to .3ds format
        # Note: trimesh exports to .3ds via its export function
        try:
            tm.export(str(output_file))
            self.logger.info(f"Successfully exported to {output_file}")
        except Exception as e:
            self.logger.warning(f"Direct .3ds export failed: {e}, exporting as OBJ instead")
            # Fallback to OBJ format which is widely supported
            obj_file = output_path / f"{filename}.obj"
            o3d.io.write_triangle_mesh(str(obj_file), mesh)
            self.logger.info(f"Exported to {obj_file} (OBJ format)")
            return str(obj_file)
        
        # Also export in additional formats for compatibility
        self._export_additional_formats(mesh, output_path, filename)
        
        return str(output_file)
    
    def _export_additional_formats(self, mesh: o3d.geometry.TriangleMesh, 
                                   output_path: Path, filename: str):
        """
        Export mesh in additional formats for better compatibility
        
        Args:
            mesh: Input mesh
            output_path: Output directory
            filename: Base filename
        """
        # Export as OBJ (widely supported)
        obj_file = output_path / f"{filename}.obj"
        o3d.io.write_triangle_mesh(str(obj_file), mesh)
        self.logger.info(f"Also exported to {obj_file}")
        
        # Export as PLY (preserves colors well)
        ply_file = output_path / f"{filename}.ply"
        o3d.io.write_triangle_mesh(str(ply_file), mesh)
        self.logger.info(f"Also exported to {ply_file}")
        
        # Export as STL (for 3D printing if needed)
        stl_file = output_path / f"{filename}.stl"
        o3d.io.write_triangle_mesh(str(stl_file), mesh)
        self.logger.info(f"Also exported to {stl_file}")
