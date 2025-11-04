# Reconstitution - 3D City Reconstruction Pipeline

Automatic 3D city reconstruction around Rambouillet (10km radius) using LiDAR HD IGN point clouds and Street View panoramic images.

## Overview

This pipeline uses AI-based segmentation to filter buildings and ground from LiDAR point clouds, generates 3D meshes, applies textures from Street View images, and exports the final model in .3ds format for use in Blender or 3ds Max.

## Features

- **LiDAR Processing**: Load and process .copc.laz point cloud files from IGN
- **Street View Integration**: Use panoramic images for texture mapping
- **AI Segmentation**: Deep learning-based point cloud segmentation (ground, buildings, vegetation)
- **3D Mesh Generation**: Multiple reconstruction algorithms (Poisson, Ball Pivoting, Alpha Shape)
- **Texture Mapping**: Apply textures from Street View images to 3D models
- **Multiple Export Formats**: .3ds, .obj, .ply, .stl

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Preparation

### LiDAR Data
Place your .copc.laz files in the `data/lidar/` directory:
```bash
mkdir -p data/lidar
# Copy your LiDAR files here
```

### Street View Images
Place your panoramic images in the `data/streetview/` directory:
```bash
mkdir -p data/streetview
# Copy your panoramic images here
```

## Configuration

Edit `config.yaml` to customize:
- Location (Rambouillet center coordinates and radius)
- Processing parameters (voxel size, filtering thresholds)
- AI model settings
- Mesh generation method
- Output format and path

## Usage

Run the complete reconstruction pipeline:
```bash
python main.py
```

The pipeline will:
1. Load and process LiDAR point clouds
2. Load Street View images
3. Segment point cloud with AI
4. Extract buildings and ground
5. Generate 3D mesh
6. Apply textures
7. Export to .3ds (and other formats)

## Output

The final 3D models will be saved in the `output/` directory:
- `rambouillet_3d_model.3ds` - Main output for 3ds Max
- `rambouillet_3d_model.obj` - OBJ format for Blender
- `rambouillet_3d_model.ply` - PLY format (preserves colors)
- `rambouillet_3d_model.stl` - STL format (3D printing)

## Pipeline Architecture

```
LiDAR Data (.copc.laz) ──┐
                         ├─> AI Segmentation ─> Mesh Generation ─> Texture Mapping ─> Export (.3ds)
Street View Images ──────┘
```

### Modules

- `lidar_processor.py` - LiDAR point cloud loading and preprocessing
- `streetview_processor.py` - Street View image loading and processing
- `segmentation.py` - AI-based point cloud segmentation
- `mesh_generator.py` - 3D mesh generation from point clouds
- `texture_mapper.py` - Texture application from images
- `exporter.py` - Model export to various formats

## AI Model

The pipeline uses a PointNet-based architecture for semantic segmentation with classes:
- Ground
- Building
- Vegetation
- Other

Pre-trained weights can be placed in `models/segmentation_weights.pth`.

## Requirements

- Python 3.8+
- Open3D
- PyTorch
- NumPy
- OpenCV
- Trimesh
- laspy (for LAZ file support)

See `requirements.txt` for complete list.

## License

MIT License

## Author

hleong75