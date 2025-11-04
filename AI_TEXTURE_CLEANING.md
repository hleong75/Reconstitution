# AI-Powered Texture Cleaning

## Overview

The Reconstitution pipeline now includes advanced AI-powered texture cleaning capabilities to automatically remove temporary elements (cars, people, bicycles, etc.) from Street View images before applying them as textures to 3D models.

## Features

### Automatic Object Detection
The AI cleaner uses a pre-trained DeepLabV3 semantic segmentation model (with MobileNetV3 backbone) to detect and classify objects in images. It specifically identifies:

- **Vehicles**: Cars, motorcycles, buses, trucks, bicycles
- **People**: Pedestrians and cyclists
- **Street Furniture**: Traffic lights, benches, parking meters, fire hydrants
- **Animals**: Birds, dogs, cats, and other animals
- **Temporary Objects**: Backpacks, umbrellas, suitcases, etc.

### Intelligent Inpainting
Once temporary objects are detected, the system uses advanced inpainting algorithms to seamlessly remove them and fill in the background. This results in cleaner, more permanent-looking textures for your 3D city models.

### Dual-Mode Operation
The texture mapper can operate in two modes:

1. **AI Mode** (default): Uses deep learning for object detection and removal
2. **Traditional CV Mode**: Falls back to computer vision techniques if AI is disabled or unavailable

## Configuration

Enable or disable AI cleaning in `config.yaml`:

```yaml
texture_mapping:
  method: "projection"
  resolution: 2048
  use_streetview: true
  interpolation: "bilinear"
  # AI-based texture cleaning configuration
  ai_cleaning:
    enabled: true  # Enable AI-powered object detection and removal
    inpaint_radius: 5  # Radius for inpainting removed objects
    model: "deeplabv3_mobilenet_v3"  # Semantic segmentation model
```

### Configuration Options

- **enabled**: Set to `true` to use AI-based cleaning, `false` to use traditional CV methods
- **inpaint_radius**: Controls the radius used for inpainting (larger = smoother but potentially blurrier)
- **model**: Specifies which segmentation model to use (currently supports `deeplabv3_mobilenet_v3`)

## Usage

The AI cleaning is automatically applied when you run the reconstruction pipeline:

```bash
python main.py
```

No code changes are required - the TextureMapper automatically uses the AI cleaner based on your configuration.

## Technical Details

### Model Architecture
- **Base Model**: DeepLabV3 with MobileNetV3-Large backbone
- **Task**: Semantic segmentation with 91 COCO classes
- **Input**: RGB images of any size (automatically resized)
- **Output**: Per-pixel classification mask

### Processing Pipeline
1. Load Street View image
2. Run semantic segmentation to identify objects
3. Create binary mask for temporary/transient objects
4. Apply morphological operations to clean mask
5. Inpaint masked regions using Navier-Stokes or TELEA method
6. Return cleaned image

### Performance Considerations
- **GPU Acceleration**: Automatically uses GPU if available via CUDA
- **Batch Processing**: Images are processed in batch for efficiency
- **Model Caching**: Model is downloaded once and cached locally
- **Fallback**: Automatically falls back to traditional CV if AI fails

## Model Download

The DeepLabV3 model is automatically downloaded from PyTorch Hub on first use:
- **Size**: ~42 MB
- **Location**: `~/.cache/torch/hub/checkpoints/`
- **Format**: Pre-trained PyTorch weights

## Benefits

### Cleaner 3D Models
By removing temporary objects, your 3D city models will:
- Look more permanent and professional
- Have fewer artifacts from transient elements
- Better represent the underlying architecture
- Be more suitable for urban planning and visualization

### Automated Workflow
- No manual image editing required
- Consistent results across all images
- Saves time in post-processing
- Scalable to large datasets

## Statistics and Monitoring

The AI cleaner provides statistics about the cleaning process:

```python
stats = ai_cleaner.get_statistics(images)
# Returns:
# {
#     'enabled': True,
#     'total_images': 100,
#     'images_with_transients': 45,
#     'total_transient_pixels': 1250000,
#     'avg_transient_percentage': 2.5
# }
```

These statistics are automatically logged during the reconstruction process.

## Comparison: AI vs Traditional CV

### AI-Based Cleaning
✅ More accurate object detection  
✅ Better handling of complex scenes  
✅ Recognizes wide variety of object types  
✅ Fewer false positives  
⚠️ Requires more computational resources  
⚠️ Initial model download required  

### Traditional CV Cleaning
✅ Faster processing  
✅ No model download needed  
✅ Works offline  
⚠️ Less accurate detection  
⚠️ More false positives/negatives  
⚠️ Limited to simpler heuristics  

## Troubleshooting

### AI Cleaning Not Working
If AI cleaning isn't working, check:
1. PyTorch and torchvision are installed
2. Internet connection for model download (first time)
3. Sufficient disk space for model cache (~50 MB)
4. Check logs for error messages

### Falling Back to Traditional CV
The system will automatically fall back to traditional CV methods if:
- AI is disabled in config
- Model fails to load
- CUDA/GPU issues occur
- Any runtime errors in AI processing

### Performance Issues
If processing is slow:
- Ensure GPU is being used (check logs for "Using device: cuda")
- Reduce image resolution in config
- Process fewer images at once
- Consider disabling AI for very large datasets

## Examples

### Before AI Cleaning
Street View images often contain:
- Parked cars obscuring building facades
- Pedestrians in front of buildings
- Temporary street furniture
- Moving vehicles

### After AI Cleaning
The cleaned images show:
- Clear building facades
- Unobstructed architecture
- Permanent structures only
- Professional, clean appearance

## Future Enhancements

Potential improvements for future versions:
- Support for additional segmentation models
- Fine-tuned models for urban scenes
- Instance segmentation for better object boundaries
- Temporal consistency across multiple views
- Custom object classes for removal

## Credits

- **Segmentation Model**: DeepLabV3 (Chen et al., 2017)
- **Backbone**: MobileNetV3 (Howard et al., 2019)
- **Framework**: PyTorch and torchvision
- **Dataset**: Pre-trained on COCO dataset
