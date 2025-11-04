# Project Summary - 3D City Reconstruction for Rambouillet

## Overview

This project provides a complete pipeline for automatically reconstructing a 3D city model around Rambouillet (10km radius) from LiDAR HD IGN point clouds (.copc.laz) and Street View panoramic images.

## Implementation Details

### Core Components

1. **LiDAR Point Cloud Processing** (`src/lidar_processor.py`)
   - Loads .copc.laz files (Cloud Optimized Point Cloud format)
   - Merges multiple point clouds
   - Filters by geographic bounds (10km around Rambouillet)
   - Downsamples using voxel grid
   - Removes statistical outliers

2. **Street View Image Processing** (`src/streetview_processor.py`)
   - Loads panoramic images (JPG/PNG)
   - Extracts EXIF metadata (GPS coordinates)
   - Resizes to standard resolution
   - Prepares for texture mapping

3. **AI-Based Segmentation** (`src/segmentation.py`)
   - PointNet neural network architecture
   - Segments point clouds into 4 classes:
     - Ground
     - Buildings
     - Vegetation
     - Other
   - Extracts building and ground points separately

4. **3D Mesh Generation** (`src/mesh_generator.py`)
   - Three reconstruction algorithms:
     - **Poisson**: Watertight meshes, smooth surfaces
     - **Ball Pivoting**: Fast, detailed features
     - **Alpha Shape**: Complex geometries
   - Mesh simplification
   - Geometry cleaning

5. **Texture Mapping** (`src/texture_mapper.py`)
   - Projects Street View images onto mesh
   - Generates UV coordinates
   - Samples colors from images
   - Creates texture atlas

6. **Model Export** (`src/exporter.py`)
   - Exports to multiple formats:
     - **.3ds** - For 3ds Max
     - **.obj** - For Blender
     - **.ply** - Preserves vertex colors
     - **.stl** - For 3D printing

### Configuration

The pipeline is fully configurable via `config.yaml`:

```yaml
location:
  name: "Rambouillet"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 10

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.05
  
  streetview:
    path: "data/streetview/"
    format: ["jpg", "png"]

processing:
  segmentation:
    model: "pointnet"
    confidence_threshold: 0.7
  
mesh_generation:
  method: "poisson"
  poisson_depth: 9
  simplification_ratio: 0.9

texture_mapping:
  resolution: 2048

output:
  format: "3ds"
  path: "output/"
  filename: "rambouillet_3d_model"
```

### File Structure

```
Reconstitution/
├── main.py                 # Main pipeline entry point
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── setup.py               # Setup script
├── demo.py                # Demo with synthetic data
├── validate.py            # Code validation script
│
├── src/                   # Source code modules
│   ├── __init__.py
│   ├── lidar_processor.py
│   ├── streetview_processor.py
│   ├── segmentation.py
│   ├── mesh_generator.py
│   ├── texture_mapper.py
│   └── exporter.py
│
├── data/                  # Input data (user-provided)
│   ├── lidar/            # .copc.laz files
│   └── streetview/       # Panoramic images
│
├── output/               # Generated 3D models
│   ├── rambouillet_3d_model.3ds
│   ├── rambouillet_3d_model.obj
│   ├── rambouillet_3d_model.ply
│   └── rambouillet_3d_model.stl
│
├── models/               # AI model weights
│   └── segmentation_weights.pth
│
└── Documentation
    ├── README.md          # English documentation
    ├── README_FR.md       # French documentation
    ├── USAGE.md          # Detailed usage guide
    ├── ARCHITECTURE.md   # Architecture overview
    ├── EXAMPLES.md       # Configuration examples
    └── LICENSE           # MIT License
```

## Usage

### Quick Start

1. **Install dependencies:**
   ```bash
   python setup.py
   ```

2. **Prepare data:**
   - Place .copc.laz files in `data/lidar/`
   - Place Street View images in `data/streetview/`

3. **Run pipeline:**
   ```bash
   python main.py
   ```

### Demo Mode

Test with synthetic data:
```bash
python demo.py create  # Create demo data
python demo.py run     # Run pipeline with demo
```

## Features

### ✓ Implemented Features

- [x] LiDAR point cloud loading and processing (.copc.laz)
- [x] Street View panoramic image loading
- [x] Geographic filtering (10km radius around Rambouillet)
- [x] Voxel-based downsampling
- [x] Outlier removal
- [x] AI-based semantic segmentation (PointNet)
- [x] Building/ground extraction
- [x] Multiple mesh reconstruction algorithms
- [x] Mesh simplification and cleaning
- [x] Texture mapping framework
- [x] Multi-format export (.3ds, .obj, .ply, .stl)
- [x] Flexible YAML configuration
- [x] Demo mode with synthetic data
- [x] Comprehensive documentation (EN + FR)

### 🚀 Future Enhancements

- [ ] Pre-trained AI model weights for IGN LiDAR data
- [ ] Advanced texture projection from Street View
- [ ] Multi-level detail (LOD) generation
- [ ] Coordinate transformation (Lambert 93 ↔ WGS84)
- [ ] Parallel processing for large datasets
- [ ] Web-based configuration interface
- [ ] Real-time progress monitoring
- [ ] Quality metrics and validation

## Dependencies

### Core Libraries
- **laspy** - LiDAR LAZ file reading
- **open3d** - Point cloud and mesh processing
- **torch** - Deep learning (PointNet)
- **numpy** - Numerical operations
- **opencv-python** - Image processing
- **trimesh** - Mesh format conversion
- **pillow** - Image I/O and EXIF
- **pyproj** - Coordinate transformations

### Optional
- **CUDA** - GPU acceleration (recommended)

## Performance

### Processing Times (estimated)

| Area | Points | Processing Time | Memory |
|------|--------|----------------|--------|
| 5 km² | 10M | 30-60 min | 8-12 GB |
| 10 km² | 50M | 60-120 min | 12-16 GB |
| 20 km² | 100M | 120-240 min | 16-24 GB |

*With GPU acceleration and voxel_size=0.05m

### Optimization Tips

1. **Increase voxel_size** for faster processing
2. **Use GPU** for 10x faster segmentation
3. **Process in chunks** for very large areas
4. **Adjust simplification_ratio** to reduce mesh size

## Technical Requirements

- Python 3.8 or higher
- 8 GB RAM minimum (16 GB recommended)
- GPU with CUDA support (optional, but recommended)
- 20+ GB disk space for data and outputs

## Validation

Run validation to check code integrity:
```bash
python validate.py
```

This checks:
- All required files present
- Python syntax validity
- Configuration structure

## Support

For questions or issues:
- Open issue on GitHub: https://github.com/hleong75/Reconstitution/issues
- See documentation: USAGE.md, ARCHITECTURE.md

## License

MIT License - See LICENSE file

## Author

hleong75

## Acknowledgments

- IGN (Institut national de l'information géographique et forestière) for LiDAR HD data
- PointNet architecture for point cloud segmentation
- Open3D library for point cloud processing
