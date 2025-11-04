#!/usr/bin/env python3
"""
Validation script to check code syntax and structure
This script validates the codebase without requiring dependencies to be installed
"""

import ast
import sys
from pathlib import Path


def validate_python_file(filepath):
    """Validate Python file syntax"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def check_required_files():
    """Check that all required files exist"""
    required_files = [
        'main.py',
        'config.yaml',
        'requirements.txt',
        'README.md',
        'README_FR.md',
        'setup.py',
        'demo.py',
        'src/__init__.py',
        'src/lidar_processor.py',
        'src/streetview_processor.py',
        'src/segmentation.py',
        'src/mesh_generator.py',
        'src/texture_mapper.py',
        'src/exporter.py',
        'USAGE.md',
        'ARCHITECTURE.md',
        'EXAMPLES.md',
        'LICENSE',
        '.gitignore'
    ]
    
    print("Checking required files...")
    all_exist = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} - MISSING")
            all_exist = False
    
    return all_exist


def validate_all_python_files():
    """Validate all Python files"""
    print("\nValidating Python files...")
    python_files = list(Path('.').rglob('*.py'))
    all_valid = True
    
    for filepath in python_files:
        if '__pycache__' in str(filepath) or 'venv' in str(filepath):
            continue
        
        valid, error = validate_python_file(filepath)
        if valid:
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} - SYNTAX ERROR: {error}")
            all_valid = False
    
    return all_valid


def check_config_structure():
    """Check config.yaml has required structure"""
    try:
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("\nValidating config.yaml structure...")
        required_keys = ['location', 'input', 'processing', 'mesh_generation', 'texture_mapping', 'output']
        all_present = True
        
        for key in required_keys:
            if key in config:
                print(f"  ✓ {key}")
            else:
                print(f"  ✗ {key} - MISSING")
                all_present = False
        
        return all_present
    except ImportError:
        print("\n⚠ PyYAML not installed, skipping config validation")
        return True
    except Exception as e:
        print(f"\n✗ Config validation failed: {e}")
        return False


def main():
    """Main validation"""
    print("=" * 60)
    print("Reconstitution Pipeline - Code Validation")
    print("=" * 60)
    print()
    
    results = []
    
    # Check required files
    results.append(("Required files", check_required_files()))
    
    # Validate Python syntax
    results.append(("Python syntax", validate_all_python_files()))
    
    # Check config
    results.append(("Config structure", check_config_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
        all_passed = all_passed and passed
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All validations passed!")
        return 0
    else:
        print("\n✗ Some validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
