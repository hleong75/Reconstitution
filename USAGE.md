# Usage Guide - 3D Reconstruction Pipeline

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution

# Run setup
python setup.py
```

### 2. Prepare Your Data

#### LiDAR Data
- Download LiDAR HD IGN data for Rambouillet region from [IGN Géoportail](https://geoservices.ign.fr/lidarhd)
- Place `.copc.laz` files in `data/lidar/` directory
- The pipeline supports Cloud Optimized Point Cloud (COPC) format

#### Street View Images
- Collect panoramic Street View images for the region
- Supported formats: JPG, PNG
- Place images in `data/streetview/` directory
- Images with GPS EXIF data work best for texture mapping

### 3. Configure the Pipeline

Edit `config.yaml`:

```yaml
location:
  name: "Rambouillet"
  center_lat: 48.6439  # Center coordinates
  center_lon: 1.8294
  radius_km: 10        # Area radius
```

### 4. Run the Pipeline

```bash
python main.py
```

## Advanced Configuration

### LiDAR Processing

```yaml
input:
  lidar:
    voxel_size: 0.05          # Downsample resolution (meters)
    min_points_per_voxel: 10  # Minimum points to keep voxel
```

**Tuning Tips:**
- Smaller `voxel_size` = more detail but slower processing
- Typical values: 0.05-0.2 meters for urban areas

### AI Segmentation

```yaml
processing:
  segmentation:
    model: "pointnet"              # or "dgcnn", "randlanet"
    confidence_threshold: 0.7       # Classification confidence
    classes:
      - "ground"
      - "building"
      - "vegetation"
      - "other"
```

**Pre-trained Models:**
- Place model weights in `models/segmentation_weights.pth`
- Models should be trained on similar LiDAR data (IGN format)

### Mesh Generation

```yaml
mesh_generation:
  method: "poisson"            # "poisson", "ball_pivoting", "alpha_shape"
  poisson_depth: 9             # 8-10 for city-scale
  simplification_ratio: 0.9    # Keep 90% of triangles
```

**Method Selection:**
- **Poisson**: Best for watertight meshes, smooth surfaces
- **Ball Pivoting**: Good for detailed features, faster
- **Alpha Shape**: Best for complex geometries

### Texture Mapping

```yaml
texture_mapping:
  method: "projection"
  resolution: 2048            # Texture resolution
  use_streetview: true
  interpolation: "bilinear"   # or "nearest", "cubic"
```

## Output Formats

The pipeline exports multiple formats:

1. **`.3ds`** - Autodesk 3ds Max native format
2. **`.obj`** - Wavefront OBJ (widely compatible)
3. **`.ply`** - Stanford PLY (preserves vertex colors)
4. **`.stl`** - Stereolithography (3D printing)

All files saved in `output/` directory.

## Pipeline Stages

### Stage 1: LiDAR Processing
- Load `.copc.laz` files
- Merge multiple point clouds
- Filter by geographic bounds (10km radius)
- Downsample and remove outliers

**Output:** Cleaned point cloud

### Stage 2: Image Processing
- Load Street View panoramic images
- Extract GPS metadata
- Resize to standard resolution

**Output:** Image dataset with metadata

### Stage 3: AI Segmentation
- Run PointNet neural network
- Classify points: ground, building, vegetation, other
- Color-code results

**Output:** Segmented point cloud

### Stage 4: Feature Extraction
- Extract building points
- Extract ground points
- Cluster and filter

**Output:** Separate building and ground clouds

### Stage 5: Mesh Generation
- Generate surface mesh using selected algorithm
- Simplify mesh
- Clean geometry

**Output:** Triangle mesh

### Stage 6: Texture Application
- Project Street View images onto mesh
- Generate UV coordinates
- Sample colors

**Output:** Textured mesh

### Stage 7: Export
- Save in multiple formats
- Generate material files
- Create metadata

**Output:** Final 3D models

## Performance Optimization

### For Large Datasets (>10 GB)

1. **Increase voxel size:**
   ```yaml
   voxel_size: 0.2  # or higher
   ```

2. **Process in chunks:**
   - Split area into smaller regions
   - Process separately and merge

3. **Use GPU acceleration:**
   - PyTorch will automatically use CUDA if available
   - Check with: `python -c "import torch; print(torch.cuda.is_available())"`

### Memory Management

- Point cloud processing: ~8GB RAM minimum
- AI segmentation: ~4GB GPU memory recommended
- Mesh generation: ~16GB RAM for large areas

## Testing with Demo Data

Don't have real data? Test with synthetic data:

```bash
# Create demo data
python demo.py create

# Run pipeline with demo
python demo.py run
```

This creates a simple synthetic city with buildings and ground.

## Troubleshooting

### Issue: "No .copc.laz files found"
**Solution:** Check file format, ensure files are in `data/lidar/`

### Issue: "CUDA out of memory"
**Solution:** 
- Reduce `voxel_size` to downsample more
- Process smaller areas
- Use CPU: set `CUDA_VISIBLE_DEVICES=-1`

### Issue: "Mesh has holes"
**Solution:**
- Switch to `method: "poisson"` 
- Increase `poisson_depth`
- Check point cloud density

### Issue: "Poor texture quality"
**Solution:**
- Increase `resolution` in texture_mapping
- Use higher quality Street View images
- Ensure images have GPS metadata

## Next Steps

1. **Refine configuration** for your specific area
2. **Train custom AI model** on your LiDAR data
3. **Adjust mesh quality** vs. performance tradeoffs
4. **Import to Blender/3ds Max** for final editing

## Support

For issues or questions, open an issue on GitHub:
https://github.com/hleong75/Reconstitution/issues
