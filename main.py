"""
3D Reconstruction Pipeline for Rambouillet
Main entry point for the reconstruction process
"""

import os
import sys
import yaml
import logging
import argparse
from typing import Dict, Any
from pathlib import Path

from src.lidar_processor import LiDARProcessor
from src.streetview_processor import StreetViewProcessor
from src.segmentation import AISegmentation
from src.mesh_generator import MeshGenerator
from src.texture_mapper import TextureMapper
from src.exporter import ModelExporter


class ReconstitutionPipeline:
    """Main pipeline for 3D city reconstruction"""
    
    def __init__(self, config_path: str = "config.yaml", city: str = None, radius_km: float = None):
        """
        Initialize the reconstruction pipeline
        
        Args:
            config_path: Path to configuration file
            city: City name (optional, overrides config)
            radius_km: Radius in kilometers (optional, overrides config)
        """
        self.config = self._load_config(config_path)
        
        # Override config with command-line parameters if provided
        if city is not None:
            self.config['location']['name'] = city
        if radius_km is not None:
            self.config['location']['radius_km'] = radius_km
            
        self._setup_logging()
        self._setup_directories()
        
        # Initialize pipeline components (no data downloader - no API usage)
        self.lidar_processor = LiDARProcessor(self.config)
        self.streetview_processor = StreetViewProcessor(self.config)
        self.segmentation = AISegmentation(self.config)
        self.mesh_generator = MeshGenerator(self.config)
        self.texture_mapper = TextureMapper(self.config)
        self.exporter = ModelExporter(self.config)
        
        self.logger.info(f"Reconstitution pipeline initialized for {self.config['location']['name']}")
        self.logger.info(f"Radius: {self.config['location']['radius_km']} km")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('reconstruction.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.config['input']['lidar']['path'],
            self.config['input']['streetview']['path'],
            self.config['output']['path'],
            'models'
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """
        Execute the complete reconstruction pipeline
        """
        self.logger.info("Starting 3D reconstruction pipeline")
        self.logger.info("Note: API usage has been disabled. Please ensure data is manually available.")
        
        try:
            # Step 1: Load and process LiDAR point clouds
            self.logger.info("Step 1: Processing LiDAR point clouds")
            point_cloud = self.lidar_processor.load_and_process()
            
            # Step 2: Load and process Street View images
            self.logger.info("Step 2: Processing Street View images")
            images = self.streetview_processor.load_images()
            
            # Step 3: Segment point cloud (ground, buildings, etc.)
            self.logger.info("Step 3: Segmenting point cloud with AI")
            segmented_cloud = self.segmentation.segment(point_cloud)
            
            # Step 4: Extract buildings and ground
            self.logger.info("Step 4: Extracting buildings and ground")
            buildings = self.segmentation.extract_buildings(segmented_cloud)
            ground = self.segmentation.extract_ground(segmented_cloud)
            
            # Step 5: Generate 3D mesh
            self.logger.info("Step 5: Generating 3D mesh")
            mesh = self.mesh_generator.generate(buildings, ground)
            
            # Step 6: Apply textures from Street View images
            self.logger.info("Step 6: Applying textures")
            textured_mesh = self.texture_mapper.apply_textures(mesh, images)
            
            # Step 7: Export to .3ds format
            self.logger.info("Step 7: Exporting to .3ds format")
            output_path = self.exporter.export_3ds(textured_mesh)
            
            self.logger.info(f"3D reconstruction completed successfully!")
            self.logger.info(f"Output file: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error in reconstruction pipeline: {str(e)}", exc_info=True)
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='3D City Reconstruction Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --city "Rambouillet" --radius 10
  python main.py --city "Paris" --radius 5 --config custom_config.yaml
        """
    )
    
    parser.add_argument('--city', type=str, help='City name for reconstruction')
    parser.add_argument('--radius', type=float, help='Radius in kilometers')
    parser.add_argument('--config', type=str, default='config.yaml', 
                       help='Path to configuration file (default: config.yaml)')
    
    args = parser.parse_args()
    
    try:
        pipeline = ReconstitutionPipeline(
            config_path=args.config,
            city=args.city,
            radius_km=args.radius
        )
        pipeline.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
