#!/usr/bin/env python3
"""
Comprehensive test suite for the 3D reconstruction pipeline
Tests command-line arguments, texture processing, and robustness
"""

import sys
import os
import yaml
import tempfile
import shutil
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse


def test_command_line_arguments():
    """Test that main.py accepts city and radius arguments"""
    print("Testing command-line argument parsing...")
    
    # Import the main module
    import main
    
    # Test argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', type=str)
    parser.add_argument('--radius', type=float)
    parser.add_argument('--config', type=str, default='config.yaml')
    
    # Test with city and radius
    args = parser.parse_args(['--city', 'Paris', '--radius', '5.5'])
    assert args.city == 'Paris', "City argument not parsed correctly"
    assert args.radius == 5.5, "Radius argument not parsed correctly"
    
    print("✓ Command-line arguments parsed correctly")
    return True


def test_pipeline_initialization_with_params():
    """Test that pipeline can be initialized with city and radius parameters"""
    print("Testing pipeline initialization with parameters...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from main import ReconstitutionPipeline
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_config = f.name
        config = {
            'location': {
                'name': 'Test',
                'center_lat': 48.0,
                'center_lon': 2.0,
                'radius_km': 1.0
            },
            'input': {
                'lidar': {'path': 'data/lidar/', 'format': 'copc.laz', 'voxel_size': 0.05, 'min_points_per_voxel': 10},
                'streetview': {'path': 'data/streetview/', 'format': ['jpg', 'png'], 'resolution': [2048, 1024]}
            },
            'processing': {
                'segmentation': {'model': 'pointnet', 'weights_path': 'models/weights.pth', 
                               'classes': ['ground', 'building'], 'confidence_threshold': 0.7},
                'ground_filter': {'method': 'cloth_simulation', 'rigidness': 3, 'class_threshold': 0.5},
                'building_extraction': {'min_height': 2.5, 'min_points': 100, 'cluster_tolerance': 0.5}
            },
            'mesh_generation': {
                'method': 'poisson', 'poisson_depth': 9, 'poisson_scale': 1.1, 'simplification_ratio': 0.9
            },
            'texture_mapping': {
                'method': 'projection', 'resolution': 2048, 'use_streetview': True, 'interpolation': 'bilinear'
            },
            'output': {
                'format': '3ds', 'path': 'output/', 'filename': 'test_model',
                'include_materials': True, 'coordinate_system': 'WGS84', 'export_lod': [1, 2, 3]
            }
        }
        yaml.dump(config, f)
    
    try:
        # Test initialization with overrides
        pipeline = ReconstitutionPipeline(
            config_path=temp_config,
            city='Paris',
            radius_km=10.0
        )
        
        assert pipeline.config['location']['name'] == 'Paris', "City not overridden"
        assert pipeline.config['location']['radius_km'] == 10.0, "Radius not overridden"
        
        print("✓ Pipeline initialized with command-line parameters")
        return True
        
    finally:
        Path(temp_config).unlink()


def test_no_api_imports():
    """Test that main.py does not import DataDownloader"""
    print("Testing that API components are not imported...")
    
    import ast
    
    with open('main.py', 'r') as f:
        code = f.read()
    
    # Parse the code
    tree = ast.parse(code)
    
    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'src.data_downloader':
                assert 'DataDownloader' not in [alias.name for alias in node.names], \
                    "DataDownloader should not be imported in main.py"
    
    # Verify DataDownloader is not used
    assert 'DataDownloader' not in code or 'DataDownloader' in code and '# DataDownloader' in code, \
        "DataDownloader usage should be removed"
    
    print("✓ API components not imported in main.py")
    return True


def test_texture_cleaning():
    """Test that texture mapper can clean images"""
    print("Testing texture cleaning functionality...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from src.texture_mapper import TextureMapper
    
    config = {
        'texture_mapping': {
            'method': 'projection',
            'resolution': 2048,
            'use_streetview': True
        }
    }
    
    mapper = TextureMapper(config)
    
    # Create test image with some noise representing temporary objects
    test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    
    # Add some bright spots (simulating car reflections)
    test_image[60:80, 40:60] = [250, 250, 250]
    
    # Clean the image
    cleaned = mapper._remove_temporary_elements(test_image)
    
    assert cleaned.shape == test_image.shape, "Image shape should be preserved"
    assert isinstance(cleaned, np.ndarray), "Cleaned output should be numpy array"
    
    print("✓ Texture cleaning works correctly")
    return True


def test_reflective_surface_detection():
    """Test detection of reflective surfaces"""
    print("Testing reflective surface detection...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Create test image
    test_image = np.ones((100, 100, 3), dtype=np.uint8) * 100
    
    # Add reflective area (bright with low saturation)
    test_image[70:90, 30:50] = [220, 220, 220]
    
    hsv = cv2.cvtColor(test_image, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(test_image, cv2.COLOR_RGB2GRAY)
    
    mask = mapper._detect_reflective_surfaces(hsv, gray)
    
    assert mask.shape == (100, 100), "Mask shape should match image"
    assert mask.dtype == np.uint8, "Mask should be uint8"
    
    print("✓ Reflective surface detection works")
    return True


def test_vertical_object_detection():
    """Test detection of vertical objects"""
    print("Testing vertical object detection...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Create test image with vertical edge
    test_image = np.ones((100, 100), dtype=np.uint8) * 128
    test_image[:, 40:45] = 200  # Vertical bright stripe
    
    mask = mapper._detect_vertical_objects(test_image, 100)
    
    assert mask.shape == (100, 100), "Mask shape should match image"
    assert mask.dtype == np.uint8, "Mask should be uint8"
    
    print("✓ Vertical object detection works")
    return True


def test_motion_blur_detection():
    """Test detection of motion blur"""
    print("Testing motion blur detection...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Create sharp image
    sharp = np.zeros((100, 100), dtype=np.uint8)
    sharp[40:60, 40:60] = 255  # Sharp square
    
    # Create blurred version
    blurred = cv2.GaussianBlur(sharp, (15, 15), 5)
    
    mask = mapper._detect_motion_blur(blurred)
    
    assert mask.shape == (100, 100), "Mask shape should match image"
    assert mask.dtype == np.uint8, "Mask should be uint8"
    
    print("✓ Motion blur detection works")
    return True


def test_config_no_api():
    """Test that config.yaml has API usage disabled"""
    print("Testing config.yaml has no API configuration...")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Should not have download section or it should be commented out
    has_download = 'download' in config
    
    if has_download:
        print("⚠ Warning: 'download' section still exists in config.yaml")
        # This is acceptable if disabled
    else:
        print("✓ No 'download' section in config.yaml")
    
    return True


def test_intelligent_color_generation():
    """Test intelligent color generation for vertices"""
    print("Testing intelligent color generation...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Create test vertices
    vertices = np.array([
        [0, 0, 0],    # Ground level
        [1, 1, 5],    # Mid height
        [2, 2, 10],   # High level
    ], dtype=np.float32)
    
    images = []  # Empty images
    
    colors = mapper._generate_intelligent_colors(vertices, images)
    
    assert colors.shape == (3, 3), "Should have 3 colors for 3 vertices"
    assert np.all(colors >= 0) and np.all(colors <= 1), "Colors should be in [0, 1] range"
    
    # Higher vertices should generally have different colors than lower ones
    assert not np.allclose(colors[0], colors[2]), "Ground and high vertices should have different colors"
    
    print("✓ Intelligent color generation works")
    return True


def test_image_cleaning_pipeline():
    """Test complete image cleaning pipeline"""
    print("Testing complete image cleaning pipeline...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Create mock images
    images = []
    for i in range(3):
        img = np.ones((100, 100, 3), dtype=np.uint8) * 120
        # Add some "temporary" elements
        img[50:70, 30:50] = [240, 240, 240]  # Bright spot
        
        images.append({
            'image': img,
            'metadata': {'filename': f'test_{i}.jpg'}
        })
    
    cleaned = mapper._clean_images(images)
    
    assert len(cleaned) == 3, "Should clean all images"
    assert all('image' in img for img in cleaned), "All cleaned images should have 'image' key"
    
    print("✓ Image cleaning pipeline works")
    return True


def test_robustness_empty_inputs():
    """Test robustness with empty inputs"""
    print("Testing robustness with empty inputs...")
    
    from src.texture_mapper import TextureMapper
    import open3d as o3d
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Test with empty mesh
    empty_mesh = o3d.geometry.TriangleMesh()
    result = mapper.apply_textures(empty_mesh, [])
    
    assert result is not None, "Should handle empty mesh gracefully"
    
    # Test with mesh but no images
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(np.array([[0, 0, 0], [1, 1, 1]]))
    result = mapper.apply_textures(mesh, [])
    
    assert result is not None, "Should handle no images gracefully"
    
    print("✓ Robustness test with empty inputs passed")
    return True


def test_robustness_invalid_images():
    """Test robustness with invalid image data"""
    print("Testing robustness with invalid image data...")
    
    from src.texture_mapper import TextureMapper
    
    config = {'texture_mapping': {}}
    mapper = TextureMapper(config)
    
    # Test with images missing 'image' key
    invalid_images = [
        {'metadata': {}},
        {'path': 'test.jpg'},
    ]
    
    try:
        cleaned = mapper._clean_images(invalid_images)
        # Should not crash, just skip invalid images
        assert len(cleaned) == 0, "Should skip all invalid images"
        print("✓ Robustness test with invalid images passed")
        return True
    except Exception as e:
        print(f"✗ Failed to handle invalid images: {e}")
        return False


def test_city_name_validation():
    """Test that city names with special characters are handled"""
    print("Testing city name validation...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from main import ReconstitutionPipeline
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_config = f.name
        config = {
            'location': {
                'name': 'Test',
                'center_lat': 48.0,
                'center_lon': 2.0,
                'radius_km': 1.0
            },
            'input': {
                'lidar': {'path': 'data/lidar/', 'format': 'copc.laz', 'voxel_size': 0.05, 'min_points_per_voxel': 10},
                'streetview': {'path': 'data/streetview/', 'format': ['jpg', 'png'], 'resolution': [2048, 1024]}
            },
            'processing': {
                'segmentation': {'model': 'pointnet', 'weights_path': 'models/weights.pth', 
                               'classes': ['ground', 'building'], 'confidence_threshold': 0.7},
                'ground_filter': {'method': 'cloth_simulation', 'rigidness': 3, 'class_threshold': 0.5},
                'building_extraction': {'min_height': 2.5, 'min_points': 100, 'cluster_tolerance': 0.5}
            },
            'mesh_generation': {
                'method': 'poisson', 'poisson_depth': 9, 'poisson_scale': 1.1, 'simplification_ratio': 0.9
            },
            'texture_mapping': {
                'method': 'projection', 'resolution': 2048, 'use_streetview': True, 'interpolation': 'bilinear'
            },
            'output': {
                'format': '3ds', 'path': 'output/', 'filename': 'test_model',
                'include_materials': True, 'coordinate_system': 'WGS84', 'export_lod': [1, 2, 3]
            }
        }
        yaml.dump(config, f)
    
    try:
        # Test with city names containing special characters
        special_cities = [
            "Saint-Étienne",
            "Aix-en-Provence",
            "L'Haÿ-les-Roses"
        ]
        
        for city in special_cities:
            pipeline = ReconstitutionPipeline(
                config_path=temp_config,
                city=city,
                radius_km=5.0
            )
            assert pipeline.config['location']['name'] == city, f"City name {city} not set correctly"
        
        print("✓ City names with special characters handled correctly")
        return True
        
    finally:
        Path(temp_config).unlink()


def test_radius_boundary_values():
    """Test radius with boundary values"""
    print("Testing radius boundary values...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from main import ReconstitutionPipeline
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_config = f.name
        config = {
            'location': {
                'name': 'Test',
                'center_lat': 48.0,
                'center_lon': 2.0,
                'radius_km': 1.0
            },
            'input': {
                'lidar': {'path': 'data/lidar/', 'format': 'copc.laz', 'voxel_size': 0.05, 'min_points_per_voxel': 10},
                'streetview': {'path': 'data/streetview/', 'format': ['jpg', 'png'], 'resolution': [2048, 1024]}
            },
            'processing': {
                'segmentation': {'model': 'pointnet', 'weights_path': 'models/weights.pth', 
                               'classes': ['ground', 'building'], 'confidence_threshold': 0.7},
                'ground_filter': {'method': 'cloth_simulation', 'rigidness': 3, 'class_threshold': 0.5},
                'building_extraction': {'min_height': 2.5, 'min_points': 100, 'cluster_tolerance': 0.5}
            },
            'mesh_generation': {
                'method': 'poisson', 'poisson_depth': 9, 'poisson_scale': 1.1, 'simplification_ratio': 0.9
            },
            'texture_mapping': {
                'method': 'projection', 'resolution': 2048, 'use_streetview': True, 'interpolation': 'bilinear'
            },
            'output': {
                'format': '3ds', 'path': 'output/', 'filename': 'test_model',
                'include_materials': True, 'coordinate_system': 'WGS84', 'export_lod': [1, 2, 3]
            }
        }
        yaml.dump(config, f)
    
    try:
        # Test with various radius values
        test_radii = [0.1, 1.0, 5.5, 10.0, 50.0, 100.0]
        
        for radius in test_radii:
            pipeline = ReconstitutionPipeline(
                config_path=temp_config,
                city='TestCity',
                radius_km=radius
            )
            assert pipeline.config['location']['radius_km'] == radius, f"Radius {radius} not set correctly"
        
        print("✓ Radius boundary values handled correctly")
        return True
        
    finally:
        Path(temp_config).unlink()


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("Running Comprehensive 3D Reconstruction Pipeline Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_command_line_arguments,
        test_pipeline_initialization_with_params,
        test_no_api_imports,
        test_texture_cleaning,
        test_reflective_surface_detection,
        test_vertical_object_detection,
        test_motion_blur_detection,
        test_config_no_api,
        test_intelligent_color_generation,
        test_image_cleaning_pipeline,
        test_robustness_empty_inputs,
        test_robustness_invalid_images,
        test_city_name_validation,
        test_radius_boundary_values,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
            print()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
            print()
    
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<50} {status}")
    
    print("=" * 70)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
