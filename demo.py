"""
Demo script to test the reconstruction pipeline with synthetic data
This creates sample point cloud data to demonstrate the pipeline without real LiDAR data
"""

import numpy as np
import open3d as o3d
import yaml
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_building(center, width, depth, height):
    """Create a simple building point cloud"""
    points = []
    
    # Base
    x_range = np.linspace(center[0] - width/2, center[0] + width/2, 20)
    y_range = np.linspace(center[1] - depth/2, center[1] + depth/2, 20)
    
    # Walls
    for x in x_range:
        for y in y_range:
            # Ground points
            points.append([x, y, center[2]])
            
            # Wall points
            if x == x_range[0] or x == x_range[-1] or y == y_range[0] or y == y_range[-1]:
                for z in np.linspace(center[2], center[2] + height, 30):
                    points.append([x, y, z])
    
    # Roof
    for x in x_range:
        for y in y_range:
            points.append([x, y, center[2] + height])
    
    return np.array(points)


def create_sample_ground(size=100, num_points=5000):
    """Create ground point cloud"""
    x = np.random.uniform(-size/2, size/2, num_points)
    y = np.random.uniform(-size/2, size/2, num_points)
    z = np.random.normal(0, 0.1, num_points)  # Slight variation in ground level
    
    return np.vstack([x, y, z]).T


def create_demo_data():
    """Create synthetic demo data"""
    logger.info("Creating demo data...")
    
    # Create directories
    Path("data/lidar").mkdir(parents=True, exist_ok=True)
    Path("data/streetview").mkdir(parents=True, exist_ok=True)
    
    # Create point cloud with buildings and ground
    all_points = []
    
    # Add ground
    ground_points = create_sample_ground()
    all_points.append(ground_points)
    
    # Add several buildings
    buildings = [
        ([10, 10, 0], 8, 6, 15),   # Building 1
        ([-15, 8, 0], 10, 8, 20),  # Building 2
        ([12, -20, 0], 6, 6, 12),  # Building 3
        ([-10, -15, 0], 12, 10, 18), # Building 4
    ]
    
    for center, width, depth, height in buildings:
        building_points = create_sample_building(center, width, depth, height)
        all_points.append(building_points)
    
    # Combine all points
    points = np.vstack(all_points)
    
    # Create point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # Add colors
    colors = np.random.rand(len(points), 3) * 0.5 + 0.3
    pcd.colors = o3d.utility.Vector3dVector(colors)
    
    # Save as PLY (since we can't easily create LAZ without specialized tools)
    output_file = "data/lidar/demo_pointcloud.ply"
    o3d.io.write_point_cloud(output_file, pcd)
    logger.info(f"Created demo point cloud: {output_file}")
    
    # Create a simple demo image
    import cv2
    demo_image = np.random.randint(100, 200, (1024, 2048, 3), dtype=np.uint8)
    cv2.imwrite("data/streetview/demo_image.jpg", demo_image)
    logger.info("Created demo Street View image: data/streetview/demo_image.jpg")
    
    logger.info("Demo data created successfully!")
    logger.info("Note: Update config.yaml to use .ply format for demo")


def run_demo():
    """Run the pipeline with demo data"""
    from main import ReconstitutionPipeline
    
    # Modify config for demo
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Update to use PLY for demo
    config['input']['lidar']['format'] = 'ply'
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    logger.info("Running reconstruction pipeline with demo data...")
    
    try:
        pipeline = ReconstitutionPipeline()
        output_path = pipeline.run()
        logger.info(f"Demo completed! Output saved to: {output_path}")
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_demo_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        run_demo()
    else:
        print("Usage:")
        print("  python demo.py create  - Create demo data")
        print("  python demo.py run     - Run pipeline with demo data")
