"""Street View image processor module"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import logging
from PIL import Image


class StreetViewProcessor:
    """Process Street View panoramic images"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Street View processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.streetview_config = config['input']['streetview']
        
    def load_images(self) -> List[Dict[str, Any]]:
        """
        Load all Street View images from the input directory
        
        Returns:
            List of image dictionaries with metadata
        """
        streetview_path = Path(self.streetview_config['path'])
        image_formats = self.streetview_config['format']
        
        image_files = []
        for fmt in image_formats:
            image_files.extend(streetview_path.glob(f"*.{fmt}"))
        
        if not image_files:
            self.logger.warning(f"No Street View images found in {streetview_path}")
            return []
        
        self.logger.info(f"Found {len(image_files)} Street View images")
        
        images = []
        for img_file in image_files:
            try:
                img_data = self._load_image(img_file)
                images.append(img_data)
            except Exception as e:
                self.logger.error(f"Error loading {img_file}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully loaded {len(images)} images")
        
        return images
    
    def _load_image(self, file_path: Path) -> Dict[str, Any]:
        """
        Load a single image and extract metadata
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary containing image data and metadata
        """
        # Load image
        img = cv2.imread(str(file_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        target_resolution = self.streetview_config['resolution']
        if img.shape[1] != target_resolution[0] or img.shape[0] != target_resolution[1]:
            img = cv2.resize(img, tuple(target_resolution), interpolation=cv2.INTER_LANCZOS4)
        
        # Extract EXIF data if available (for GPS coordinates)
        metadata = self._extract_metadata(file_path)
        
        return {
            'path': str(file_path),
            'image': img,
            'shape': img.shape,
            'metadata': metadata
        }
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from image (GPS, orientation, etc.)
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'filename': file_path.name,
            'gps': None,
            'orientation': None
        }
        
        try:
            # Try to extract EXIF data
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            img = Image.open(file_path)
            exif = img._getexif()
            
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'GPSInfo':
                        gps_data = {}
                        for t in value:
                            sub_tag = GPSTAGS.get(t, t)
                            gps_data[sub_tag] = value[t]
                        metadata['gps'] = gps_data
                    elif tag == 'Orientation':
                        metadata['orientation'] = value
        except Exception as e:
            self.logger.debug(f"Could not extract EXIF from {file_path}: {str(e)}")
        
        return metadata
