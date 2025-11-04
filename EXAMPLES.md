# Example Configurations

## 1. High Quality - Maximum Detail

For maximum detail when processing small areas (<5 km²):

```yaml
location:
  name: "Rambouillet_HighQuality"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 2

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.02  # Very fine detail
    min_points_per_voxel: 5
  
  streetview:
    path: "data/streetview/"
    format: ["jpg", "png"]
    resolution: [4096, 2048]  # High resolution

processing:
  segmentation:
    model: "pointnet"
    confidence_threshold: 0.8  # Higher confidence
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 3
    class_threshold: 0.5

mesh_generation:
  method: "poisson"
  poisson_depth: 10  # Maximum detail
  poisson_scale: 1.1
  simplification_ratio: 0.95  # Keep 95% of triangles
  
texture_mapping:
  method: "projection"
  resolution: 4096  # High resolution textures
  use_streetview: true
  interpolation: "cubic"

output:
  format: "3ds"
  path: "output/high_quality/"
  filename: "rambouillet_hq"
```

## 2. Fast Preview - Low Quality

For quick previews and testing:

```yaml
location:
  name: "Rambouillet_Preview"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 10

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.5  # Aggressive downsampling
    min_points_per_voxel: 20
  
  streetview:
    path: "data/streetview/"
    format: ["jpg"]
    resolution: [1024, 512]  # Lower resolution

processing:
  segmentation:
    model: "pointnet"
    confidence_threshold: 0.6  # More permissive
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 2
    class_threshold: 0.5

mesh_generation:
  method: "ball_pivoting"  # Faster method
  simplification_ratio: 0.5  # Keep only 50%
  
texture_mapping:
  method: "projection"
  resolution: 1024
  use_streetview: true
  interpolation: "nearest"  # Fastest

output:
  format: "3ds"
  path: "output/preview/"
  filename: "rambouillet_preview"
```

## 3. Balanced - Production Quality

Balanced settings for production use:

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
    voxel_size: 0.05  # Good balance
    min_points_per_voxel: 10
  
  streetview:
    path: "data/streetview/"
    format: ["jpg", "png"]
    resolution: [2048, 1024]

processing:
  segmentation:
    model: "pointnet"
    weights_path: "models/segmentation_weights.pth"
    classes:
      - "ground"
      - "building"
      - "vegetation"
      - "other"
    confidence_threshold: 0.7
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 3
    class_threshold: 0.5
  
  building_extraction:
    min_height: 2.5
    min_points: 100
    cluster_tolerance: 0.5

mesh_generation:
  method: "poisson"
  poisson_depth: 9
  poisson_scale: 1.1
  simplification_ratio: 0.9
  
texture_mapping:
  method: "projection"
  resolution: 2048
  use_streetview: true
  interpolation: "bilinear"

output:
  format: "3ds"
  path: "output/"
  filename: "rambouillet_3d_model"
  include_materials: true
  coordinate_system: "WGS84"
  export_lod: [1, 2, 3]
```

## 4. Large Area - Memory Efficient

For very large areas (>50 km²):

```yaml
location:
  name: "Rambouillet_Extended"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 20  # Large area

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.2  # More aggressive downsampling
    min_points_per_voxel: 15
  
  streetview:
    path: "data/streetview/"
    format: ["jpg"]
    resolution: [1024, 512]

processing:
  segmentation:
    model: "pointnet"
    confidence_threshold: 0.7
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 2
    class_threshold: 0.5
  
  building_extraction:
    min_height: 3.0  # Filter small structures
    min_points: 200
    cluster_tolerance: 1.0

mesh_generation:
  method: "ball_pivoting"  # More memory efficient
  simplification_ratio: 0.7  # More aggressive simplification
  
texture_mapping:
  method: "projection"
  resolution: 1024
  use_streetview: false  # Skip textures to save memory
  interpolation: "nearest"

output:
  format: "3ds"
  path: "output/extended/"
  filename: "rambouillet_extended"
  export_lod: [1]  # Only one LOD
```

## 5. Building-Only Mode

Extract and reconstruct only buildings:

```yaml
location:
  name: "Rambouillet_BuildingsOnly"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 5

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.05
    min_points_per_voxel: 10
  
  streetview:
    path: "data/streetview/"
    format: ["jpg", "png"]
    resolution: [2048, 1024]

processing:
  segmentation:
    model: "pointnet"
    classes:
      - "ground"
      - "building"  # Focus on buildings
      - "vegetation"
      - "other"
    confidence_threshold: 0.75  # Higher threshold for buildings
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 3
    class_threshold: 0.3  # More strict ground filtering
  
  building_extraction:
    min_height: 2.5
    min_points: 50
    cluster_tolerance: 0.3  # Tighter clustering

mesh_generation:
  method: "poisson"
  poisson_depth: 9
  poisson_scale: 1.2  # Slightly larger scale for buildings
  simplification_ratio: 0.95  # Keep detail on buildings
  
texture_mapping:
  method: "projection"
  resolution: 2048
  use_streetview: true
  interpolation: "bilinear"

output:
  format: "3ds"
  path: "output/buildings/"
  filename: "rambouillet_buildings"
```

## 6. Terrain-Only Mode

Generate detailed terrain/ground model:

```yaml
location:
  name: "Rambouillet_Terrain"
  center_lat: 48.6439
  center_lon: 1.8294
  radius_km: 15

input:
  lidar:
    format: "copc.laz"
    path: "data/lidar/"
    voxel_size: 0.1  # Balance detail and coverage
    min_points_per_voxel: 5
  
  streetview:
    path: "data/streetview/"
    format: ["jpg"]
    resolution: [1024, 512]

processing:
  segmentation:
    model: "pointnet"
    classes:
      - "ground"  # Focus on ground
      - "building"
      - "vegetation"
      - "other"
    confidence_threshold: 0.6
  
  ground_filter:
    method: "cloth_simulation"
    rigidness: 1  # More flexible for terrain
    class_threshold: 0.7  # More permissive for ground

mesh_generation:
  method: "alpha_shape"  # Better for natural terrain
  simplification_ratio: 0.85
  
texture_mapping:
  method: "projection"
  resolution: 1024
  use_streetview: false
  interpolation: "bilinear"

output:
  format: "3ds"
  path: "output/terrain/"
  filename: "rambouillet_terrain"
```

## Configuration Tips

### Choosing Voxel Size
- **Urban areas with detail**: 0.02-0.05m
- **Standard reconstruction**: 0.05-0.1m
- **Large areas/preview**: 0.2-0.5m

### Choosing Mesh Method
- **Poisson**: Watertight, smooth buildings
- **Ball Pivoting**: Fast, detailed features
- **Alpha Shape**: Natural terrain, irregular shapes

### Choosing Simplification Ratio
- **High quality**: 0.9-0.95 (keep 90-95%)
- **Standard**: 0.7-0.9 (keep 70-90%)
- **Preview/Large area**: 0.3-0.7 (keep 30-70%)

### Memory Estimates

| Area | Voxel Size | Expected Memory | Processing Time |
|------|-----------|----------------|-----------------|
| 5 km²| 0.05m     | 8-12 GB        | 30-60 min       |
| 10 km²| 0.1m     | 12-16 GB       | 60-120 min      |
| 20 km²| 0.2m     | 16-24 GB       | 120-240 min     |

### GPU vs CPU

With GPU (CUDA):
- Segmentation: 10x faster
- Texture mapping: 3x faster

Without GPU:
- Still works, just slower
- Recommended for areas <5 km²
