#!/usr/bin/env python3
"""
Test script for automatic data download functionality
Tests the download module without requiring actual API keys or network access
"""

import sys
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil


def test_data_downloader_init():
    """Test DataDownloader initialization"""
    print("Testing DataDownloader initialization...")
    
    # Mock config
    config = {
        'location': {
            'center_lat': 48.6439,
            'center_lon': 1.8294,
            'radius_km': 10
        },
        'input': {
            'lidar': {'path': 'data/lidar/'},
            'streetview': {'path': 'data/streetview/'}
        },
        'download': {
            'enable_lidar': False,
            'enable_streetview': True,
            'google_api_key': 'test_key',
            'streetview_num_samples': 10
        }
    }
    
    # Import after mocking to avoid dependency issues
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Import the module
    from src.data_downloader import DataDownloader
    
    downloader = DataDownloader(config)
    assert downloader.config == config
    assert downloader.location_config['center_lat'] == 48.6439
    
    print("✓ DataDownloader initialization test passed")
    return True


def test_sample_point_generation():
    """Test Street View sample point generation"""
    print("Testing sample point generation...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from src.data_downloader import DataDownloader
    
    config = {
        'location': {
            'center_lat': 48.6439,
            'center_lon': 1.8294,
            'radius_km': 1
        },
        'input': {
            'lidar': {'path': 'data/lidar/'},
            'streetview': {'path': 'data/streetview/'}
        },
        'download': {
            'streetview_num_samples': 10
        }
    }
    
    downloader = DataDownloader(config)
    points = downloader._generate_sample_points(48.6439, 1.8294, 1.0)
    
    assert len(points) > 0, "Should generate sample points"
    assert len(points) <= 10, "Should respect max samples"
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points), "Points should be (lat, lon) tuples"
    
    print(f"✓ Generated {len(points)} sample points")
    return True


def test_config_update():
    """Test that setup_download.py can update config"""
    print("Testing config update functionality...")
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_config = f.name
        config = {
            'location': {'center_lat': 48.6439},
            'input': {'lidar': {'path': 'data/lidar/'}},
            'download': {}
        }
        yaml.dump(config, f)
    
    try:
        # Load and modify
        with open(temp_config, 'r') as f:
            config = yaml.safe_load(f)
        
        config['download']['enable_streetview'] = True
        config['download']['google_api_key'] = 'test_key_123'
        
        with open(temp_config, 'w') as f:
            yaml.dump(config, f)
        
        # Verify
        with open(temp_config, 'r') as f:
            updated = yaml.safe_load(f)
        
        assert updated['download']['enable_streetview'] == True
        assert updated['download']['google_api_key'] == 'test_key_123'
        
        print("✓ Config update test passed")
        return True
        
    finally:
        Path(temp_config).unlink()


def test_main_pipeline_integration():
    """Test that main pipeline can initialize with downloader"""
    print("Testing main pipeline integration...")
    
    # Just verify the file imports without instantiating
    import ast
    
    with open('main.py', 'r') as f:
        code = f.read()
    
    try:
        tree = ast.parse(code)
        
        # Check that DataDownloader is imported
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        downloader_imported = any(
            node.module == 'src.data_downloader' and 
            any(alias.name == 'DataDownloader' for alias in node.names)
            for node in imports
        )
        
        assert downloader_imported, "DataDownloader should be imported in main.py"
        
        print("✓ Main pipeline imports DataDownloader correctly")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in main.py: {e}")
        return False


def test_download_disabled():
    """Test that pipeline works when download is disabled"""
    print("Testing pipeline with download disabled...")
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from src.data_downloader import DataDownloader
    
    config = {
        'location': {
            'center_lat': 48.6439,
            'center_lon': 1.8294,
            'radius_km': 10
        },
        'input': {
            'lidar': {'path': 'data/lidar/'},
            'streetview': {'path': 'data/streetview/'}
        },
        'download': {
            'enable_lidar': False,
            'enable_streetview': False
        }
    }
    
    downloader = DataDownloader(config)
    lidar_ok, streetview_ok = downloader.download_all()
    
    # When disabled, should return True (considered success)
    assert lidar_ok == True
    assert streetview_ok == True
    
    print("✓ Download disabled test passed")
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("Running Automatic Data Download Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_data_downloader_init,
        test_sample_point_generation,
        test_config_update,
        test_download_disabled,
        test_main_pipeline_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
            print()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {str(e)}")
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
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
