# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT DATA SOURCES                        │
├─────────────────────────────────────────────────────────────┤
│  LiDAR Point Clouds        │    Street View Images          │
│  (.copc.laz files)         │    (panoramic JPG/PNG)         │
│  - IGN HD format           │    - GPS tagged                │
│  - Lambert 93 coords       │    - High resolution           │
└──────────┬─────────────────┴────────────┬──────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────┐      ┌──────────────────────┐
│  LiDAR Processor     │      │ StreetView Processor │
│  - Load LAZ files    │      │ - Load images        │
│  - Merge clouds      │      │ - Extract metadata   │
│  - Filter location   │      │ - Resize/normalize   │
│  - Downsample        │      │ - GPS extraction     │
│  - Remove outliers   │      │                      │
└──────────┬───────────┘      └──────────┬───────────┘
           │                               │
           └──────────┬────────────────────┘
                      ▼
           ┌─────────────────────┐
           │  AI Segmentation    │
           │  - PointNet model   │
           │  - Classify points  │
           │    * Ground         │
           │    * Buildings      │
           │    * Vegetation     │
           │    * Other          │
           └──────────┬──────────┘
                      ▼
           ┌─────────────────────┐
           │ Feature Extraction  │
           │ - Extract buildings │
           │ - Extract ground    │
           │ - Cluster objects   │
           └──────────┬──────────┘
                      ▼
           ┌─────────────────────┐
           │  Mesh Generator     │
           │ - Poisson recon     │
           │ - Ball pivoting     │
           │ - Alpha shape       │
           │ - Simplification    │
           │ - Cleaning          │
           └──────────┬──────────┘
                      ▼
           ┌─────────────────────┐
           │  Texture Mapper     │
           │ - Project images    │
           │ - UV mapping        │
           │ - Color sampling    │
           │ - Atlas generation  │
           └──────────┬──────────┘
                      ▼
           ┌─────────────────────┐
           │   Model Exporter    │
           │ - .3ds format       │
           │ - .obj format       │
           │ - .ply format       │
           │ - .stl format       │
           └──────────┬──────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     OUTPUT FILES                             │
├─────────────────────────────────────────────────────────────┤
│  rambouillet_3d_model.3ds  - Main output for 3ds Max       │
│  rambouillet_3d_model.obj  - OBJ for Blender               │
│  rambouillet_3d_model.ply  - PLY with colors               │
│  rambouillet_3d_model.stl  - STL for 3D printing           │
└─────────────────────────────────────────────────────────────┘
```

## Module Details

### 1. LiDAR Processor (`src/lidar_processor.py`)

**Purpose:** Load and preprocess LiDAR point cloud data

**Key Functions:**
- `load_and_process()` - Main processing pipeline
- `_load_laz_file()` - Read individual LAZ files
- `_filter_by_location()` - Geographic filtering

**Technologies:**
- `laspy` - LAZ file reading
- `open3d` - Point cloud manipulation
- `numpy` - Numerical operations

**Output:** Open3D PointCloud object

### 2. Street View Processor (`src/streetview_processor.py`)

**Purpose:** Load and process panoramic images

**Key Functions:**
- `load_images()` - Load all images
- `_load_image()` - Load single image
- `_extract_metadata()` - Extract EXIF/GPS data

**Technologies:**
- `opencv-python` - Image processing
- `pillow` - EXIF extraction

**Output:** List of image dictionaries with metadata

### 3. AI Segmentation (`src/segmentation.py`)

**Purpose:** Classify point cloud points using deep learning

**Architecture:**
```
Input: (N, 3) point cloud
       ↓
Feature Extraction:
- Conv1D(3 → 64)
- Conv1D(64 → 128)
- Conv1D(128 → 1024)
       ↓
Global Feature:
- MaxPool
- Expand to all points
       ↓
Segmentation Head:
- Conv1D(1088 → 512)
- Conv1D(512 → 256)
- Conv1D(256 → num_classes)
       ↓
Output: (N, 4) class probabilities
```

**Key Functions:**
- `segment()` - Run segmentation
- `extract_buildings()` - Extract building points
- `extract_ground()` - Extract ground points

**Technologies:**
- `PyTorch` - Deep learning framework
- PointNet architecture

**Output:** Segmented point cloud with labels

### 4. Mesh Generator (`src/mesh_generator.py`)

**Purpose:** Convert point clouds to triangle meshes

**Algorithms:**

1. **Poisson Reconstruction**
   - Watertight meshes
   - Smooth surfaces
   - Best for buildings

2. **Ball Pivoting**
   - Detail preservation
   - Faster processing
   - Good for complex geometry

3. **Alpha Shape**
   - Concave hulls
   - Sharp features
   - Best for irregular objects

**Key Functions:**
- `generate()` - Main mesh generation
- `_poisson_reconstruction()` - Poisson method
- `_ball_pivoting()` - Ball pivoting method
- `_alpha_shape()` - Alpha shape method
- `_simplify_mesh()` - Reduce polygon count

**Technologies:**
- `open3d` - Mesh reconstruction

**Output:** Open3D TriangleMesh

### 5. Texture Mapper (`src/texture_mapper.py`)

**Purpose:** Apply textures from Street View images

**Process:**
1. Project 3D vertices to 2D image coordinates
2. Sample colors from images
3. Generate UV coordinates
4. Create texture atlas

**Key Functions:**
- `apply_textures()` - Main texturing pipeline
- `_project_vertex_to_image()` - 3D to 2D projection
- `_sample_color_from_image()` - Color sampling

**Technologies:**
- `opencv-python` - Image operations
- Camera projection math

**Output:** Textured mesh

### 6. Model Exporter (`src/exporter.py`)

**Purpose:** Export meshes to various formats

**Supported Formats:**
- **.3ds** - Autodesk 3ds Max
- **.obj** - Wavefront (Blender, etc.)
- **.ply** - Stanford (with colors)
- **.stl** - 3D printing

**Key Functions:**
- `export_3ds()` - Export to .3ds
- `_export_additional_formats()` - Export all formats

**Technologies:**
- `trimesh` - Format conversion
- `open3d` - Mesh I/O

**Output:** Multiple format files

## Data Flow

### Point Cloud Processing Flow

```
Raw LAZ → Load → Merge → Filter → Downsample → Clean → Segmented Cloud
  ↓        ↓      ↓       ↓         ↓           ↓         ↓
10GB      8GB    6GB     4GB       1GB        800MB     800MB
```

### Mesh Generation Flow

```
Point Cloud → Normal Estimation → Surface Reconstruction → Simplification
    ↓              ↓                      ↓                      ↓
  800MB          1GB                    3GB                    1GB
```

## Performance Characteristics

### Time Complexity

| Stage               | Complexity    | 1M points | 10M points |
|---------------------|---------------|-----------|------------|
| Loading             | O(n)          | 5s        | 50s        |
| Downsampling        | O(n log n)    | 3s        | 40s        |
| Segmentation        | O(n)          | 20s       | 200s       |
| Mesh Generation     | O(n²)         | 60s       | 600s       |
| Texture Mapping     | O(n·m)        | 30s       | 300s       |
| Export              | O(n)          | 5s        | 50s        |

### Memory Requirements

| Stage               | Memory per 1M points |
|---------------------|---------------------|
| Point Cloud         | 100 MB              |
| Segmentation        | 500 MB              |
| Mesh Generation     | 300 MB              |
| Texture Mapping     | 200 MB              |

## Configuration System

The pipeline uses YAML configuration with hierarchical structure:

```yaml
location:        # Geographic bounds
input:           # Data sources
processing:      # Algorithm parameters
mesh_generation: # Reconstruction settings
texture_mapping: # Texture settings
output:          # Export configuration
```

All modules read from this central configuration.

## Extension Points

### Add New Segmentation Model

1. Implement model in `src/segmentation.py`
2. Add to config: `processing.segmentation.model`
3. Load appropriate weights

### Add New Mesh Algorithm

1. Implement in `src/mesh_generator.py`
2. Add method to `_generate()` switch
3. Configure in `mesh_generation.method`

### Add New Export Format

1. Implement in `src/exporter.py`
2. Add format conversion
3. Update documentation

## Dependencies Graph

```
main.py
  ├── lidar_processor
  │     ├── laspy
  │     ├── open3d
  │     └── numpy
  ├── streetview_processor
  │     ├── opencv-python
  │     ├── pillow
  │     └── numpy
  ├── segmentation
  │     ├── torch
  │     ├── open3d
  │     └── numpy
  ├── mesh_generator
  │     ├── open3d
  │     └── numpy
  ├── texture_mapper
  │     ├── opencv-python
  │     └── numpy
  └── exporter
        ├── trimesh
        └── open3d
```
