# Automatic Data Download Guide

This guide explains how to use the automatic data download feature for the Reconstitution pipeline.

## Overview

The Reconstitution pipeline can automatically download:
1. **Street View panoramic images** using Google Street View Static API
2. **LiDAR data** from IGN Géoportail (limited automation)

## Quick Start

### 1. Configure Automatic Download

Run the interactive setup:
```bash
python setup_download.py config
```

This will:
- Ask if you want to enable LiDAR download
- Ask if you want to enable Street View download
- Request your Google Maps API key (for Street View)
- Configure download parameters (number of images, resolution)

### 2. Run the Pipeline

Once configured, just run:
```bash
python main.py
```

The pipeline will automatically download data before processing if enabled.

## Street View Download Setup

### Getting a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Street View Static API**
4. Go to **Credentials** and create an API key
5. Enable billing (required for Street View API)

**Note:** Google provides a monthly free credit that covers ~28,000 Street View image requests.

### Configure in config.yaml

Either use the interactive setup or manually edit `config.yaml`:

```yaml
download:
  enable_streetview: true
  google_api_key: "YOUR_API_KEY_HERE"
  streetview_size: "2048x1024"  # Image resolution
  streetview_num_samples: 50    # Number of images to download
```

### Image Resolution Options

- `640x640` - Small, faster downloads
- `1024x512` - Medium quality
- `2048x1024` - High quality (recommended)
- `4096x2048` - Maximum quality (higher cost)

## LiDAR Download

### Current Status

Automatic LiDAR download is **limited** due to:
- IGN's data distribution requires authentication
- Large file sizes (hundreds of MB to GB per tile)
- Complex tile selection logic

### Recommended: Manual Download

1. Visit [IGN LiDAR HD](https://geoservices.ign.fr/lidarhd)
2. Navigate to your area of interest
3. Download `.copc.laz` files
4. Place files in `data/lidar/` directory

### Future Enhancement

Automatic LiDAR download will be improved in future releases to support:
- IGN API authentication
- Automatic tile selection based on coordinates
- Parallel downloads for large areas

## Download Configuration Reference

Full configuration options in `config.yaml`:

```yaml
download:
  # Enable/disable automatic downloads
  enable_lidar: false
  enable_streetview: true
  
  # Google Street View API
  google_api_key: "your_key_here"
  streetview_size: "2048x1024"
  streetview_num_samples: 50
  
  # IGN LiDAR (for future use)
  lidar_url: "https://wxs.ign.fr/decouverte/telechargement/prepackage/LIDARHD_PACK_"
```

## Download Behavior

### Area Coverage

Street View images are sampled in a grid pattern:
- Center: Configured location (e.g., Rambouillet center)
- Radius: Configured radius (e.g., 10 km)
- Spacing: Approximately 100-200 meters between samples

### Sampling Strategy

For a 10 km radius with 50 samples:
- Grid spacing: ~1-2 km
- Only locations with available Street View are downloaded
- Failed downloads are logged but don't stop the pipeline

### Rate Limiting

The downloader includes:
- 0.5 second delay between requests (respects API limits)
- Automatic retry on transient failures
- Skips already downloaded images

## Cost Estimation

### Google Street View Static API

Pricing (as of 2024):
- First 28,000 requests/month: FREE
- Additional requests: $7.00 per 1,000

Example costs:
- 50 images: FREE
- 100 images: FREE  
- 500 images: FREE
- 1,000 images: FREE
- 10,000 images: FREE
- 50,000 images: ~$154

**Tip:** Start with 50-100 images for initial testing.

## Troubleshooting

### "Google API key not configured"

**Solution:** Run `python setup_download.py config` or edit `config.yaml` manually.

### "No Street View at location"

**Cause:** Street View not available at that location.

**Solution:** This is normal. The downloader will skip unavailable locations.

### Downloads are slow

**Cause:** Large number of samples or slow network.

**Solutions:**
- Reduce `streetview_num_samples` in config
- Use smaller image size (e.g., 1024x512)
- Run overnight for large areas

### "Quota exceeded" error

**Cause:** Exceeded daily API quota.

**Solutions:**
- Wait 24 hours for quota reset
- Increase quota in Google Cloud Console
- Enable billing if not already enabled

### Downloads incomplete

**Cause:** Network issues or API problems.

**Solution:** Re-run the pipeline - it will skip existing images.

## Advanced Usage

### Command Line Control

Disable auto-download for a single run:
```python
from main import ReconstitutionPipeline

pipeline = ReconstitutionPipeline()
pipeline.run(auto_download=False)
```

### Custom Download Script

For more control, use the downloader directly:

```python
from src.data_downloader import DataDownloader
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

downloader = DataDownloader(config)

# Download only Street View
downloader.download_streetview_data()

# Or download both
lidar_ok, sv_ok = downloader.download_all()
```

### Verify Downloads

Check downloaded files:
```bash
# Count Street View images
ls -1 data/streetview/*.jpg | wc -l

# Check file sizes
du -sh data/streetview/
du -sh data/lidar/
```

## Alternative: streetget Tool

For advanced users, consider using the [streetget](https://www.di.ens.fr/willow/research/streetget/) tool for downloading with depth information.

Refer to the streetget documentation for installation and usage instructions.

Benefits of streetget:
- Downloads depth maps (3D information)
- Batch processing optimized
- Advanced filtering options

## Data Management

### Organizing Downloads

Recommended directory structure:
```
data/
├── streetview/
│   ├── streetview_0001_48.643900_1.829400.jpg
│   ├── streetview_0001_48.643900_1.829400.json  # Metadata
│   ├── streetview_0002_48.644500_1.830100.jpg
│   └── ...
└── lidar/
    ├── LIDARHD_XXXXX.copc.laz
    └── ...
```

### Cleaning Up

Remove downloaded data:
```bash
# Remove all Street View images
rm -rf data/streetview/*

# Remove LiDAR data
rm -rf data/lidar/*

# Note: The data directories are git-ignored, so git clean won't affect them
```

### Backup

Backup downloaded data to avoid re-downloading:
```bash
# Create backup
tar -czf data_backup.tar.gz data/

# Restore from backup
tar -xzf data_backup.tar.gz
```

## Best Practices

1. **Start Small**: Test with 10-20 images first
2. **Check Costs**: Monitor API usage in Google Cloud Console
3. **Verify Coverage**: Check that images cover your area
4. **Local Backup**: Keep a backup of downloaded data
5. **Rate Limits**: Don't download thousands of images in one session

## FAQ

**Q: Is automatic download required?**
A: No. You can manually download data and disable auto-download.

**Q: Can I use free alternatives to Google Street View?**
A: Yes. Mapillary and other services provide street-level imagery. You'll need to adapt the downloader.

**Q: How much data will be downloaded?**
A: For 50 Street View images at 2048x1024: ~50-100 MB. LiDAR files are much larger (1-5 GB per tile).

**Q: Can I download for any location?**
A: Street View: Yes, where available. LiDAR: Only areas covered by IGN (France).

**Q: What if download fails mid-process?**
A: Re-run the pipeline. It will skip already downloaded files.

## Support

For issues with automatic download:
1. Check this guide
2. Review error messages in `reconstruction.log`
3. Open an issue on GitHub with logs

## References

- [Google Street View Static API](https://developers.google.com/maps/documentation/streetview)
- [streetget tool](https://www.di.ens.fr/willow/research/streetget/)
- [IGN LiDAR HD](https://geoservices.ign.fr/lidarhd)
