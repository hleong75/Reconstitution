# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/hleong75/Reconstitution.git
cd Reconstitution

# 2. Run setup
python setup.py
```

## Test with Demo Data (5 minutes)

```bash
# Create synthetic demo data
python demo.py create

# Run the pipeline
python demo.py run
```

Output will be in `output/` directory.

## Use with Real Data

### Step 1: Get LiDAR Data

Download LiDAR HD IGN data:
- Visit: https://geoservices.ign.fr/lidarhd
- Search for "Rambouillet"
- Download .copc.laz files
- Place in `data/lidar/`

### Step 2: Get Street View Images

Collect panoramic images:
- Use Google Street View or similar
- Save as JPG or PNG
- Ideally with GPS EXIF data
- Place in `data/streetview/`

### Step 3: Configure

Edit `config.yaml` if needed:
```yaml
location:
  center_lat: 48.6439  # Rambouillet center
  center_lon: 1.8294
  radius_km: 10        # Adjust as needed
```

### Step 4: Run

```bash
python main.py
```

### Step 5: View Results

Open with:
- **Blender**: Import `.obj` or `.ply` file
- **3ds Max**: Import `.3ds` file
- **MeshLab**: Open any format for preview

## Configuration Quick Reference

### Fast Preview
```yaml
voxel_size: 0.5
method: "ball_pivoting"
simplification_ratio: 0.5
```

### High Quality
```yaml
voxel_size: 0.02
method: "poisson"
poisson_depth: 10
simplification_ratio: 0.95
```

### Balanced (Recommended)
```yaml
voxel_size: 0.05
method: "poisson"
poisson_depth: 9
simplification_ratio: 0.9
```

## Troubleshooting

### "No module named 'laspy'"
**Fix:** Run `python setup.py` or `pip install -r requirements.txt`

### "CUDA out of memory"
**Fix:** Increase `voxel_size` in config.yaml or use CPU

### Pipeline runs but output is empty
**Fix:** Check that data files are in correct directories:
- `data/lidar/*.copc.laz`
- `data/streetview/*.jpg`

### Need help?
See detailed documentation:
- **USAGE.md** - Complete usage guide
- **EXAMPLES.md** - Configuration examples
- **ARCHITECTURE.md** - Technical details

## Next Steps

1. Read **USAGE.md** for detailed instructions
2. Try different configurations from **EXAMPLES.md**
3. Adjust for your specific area and quality needs
4. Import results into Blender/3ds Max for final touches

## Support

Open an issue: https://github.com/hleong75/Reconstitution/issues
