"""
3D Reconstruction Pipeline for Rambouillet
Main entry point for the reconstruction process
"""

import os
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

from src.lidar_processor import LiDARProcessor
from src.streetview_processor import StreetViewProcessor
from src.segmentation import AISegmentation
from src.mesh_generator import MeshGenerator
from src.texture_mapper import TextureMapper
from src.exporter import ModelExporter
from src.data_downloader import DataDownloader


class ReconstitutionPipeline:
    """Main pipeline for 3D city reconstruction"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the reconstruction pipeline
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
        # Initialize pipeline components
        self.data_downloader = DataDownloader(self.config)
        self.lidar_processor = LiDARProcessor(self.config)
        self.streetview_processor = StreetViewProcessor(self.config)
        self.segmentation = AISegmentation(self.config)
        self.mesh_generator = MeshGenerator(self.config)
        self.texture_mapper = TextureMapper(self.config)
        self.exporter = ModelExporter(self.config)
        
        self.logger.info("Reconstitution pipeline initialized")
    
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
    
    def run(self, auto_download=True):
        """
        Execute the complete reconstruction pipeline
        
        Args:
            auto_download: Whether to automatically download data if enabled in config
        """
        self.logger.info("Starting 3D reconstruction pipeline")
        
        try:
            # Step 0: Download data if auto-download is enabled
            if auto_download:
                download_config = self.config.get('download', {})
                if download_config.get('enable_lidar') or download_config.get('enable_streetview'):
                    self.logger.info("Step 0: Downloading data automatically")
                    lidar_ok, streetview_ok = self.data_downloader.download_all()
                    if not lidar_ok and download_config.get('enable_lidar'):
                        self.logger.warning("LiDAR download incomplete, continuing with existing data")
                    if not streetview_ok and download_config.get('enable_streetview'):
                        self.logger.warning("Street View download incomplete, continuing with existing data")
            
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
    pipeline = ReconstitutionPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
