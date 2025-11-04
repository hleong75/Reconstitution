#!/usr/bin/env python3
"""
Setup script to prepare the environment
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        sys.exit(1)


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    directories = [
        "data/lidar",
        "data/streetview",
        "output",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {directory}")
    
    print("✓ Directories created")


def check_gpu():
    """Check if GPU is available for PyTorch"""
    print("\nChecking GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠ No GPU detected, will use CPU (slower)")
    except ImportError:
        print("⚠ PyTorch not installed yet")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Reconstitution 3D City Reconstruction - Setup")
    print("=" * 60)
    
    check_python_version()
    install_dependencies()
    create_directories()
    check_gpu()
    
    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Place your .copc.laz files in data/lidar/")
    print("2. Place your Street View images in data/streetview/")
    print("3. Configure settings in config.yaml")
    print("4. Run: python main.py")
    print("\nOr run demo with synthetic data:")
    print("  python demo.py create")
    print("  python demo.py run")


if __name__ == "__main__":
    main()
