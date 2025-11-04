"""AI-based texture cleaning module for removing temporary elements from Street View images"""

import numpy as np
import cv2
import torch
import torch.nn as nn
from typing import Dict, Any, List, Tuple, Optional
import logging
from pathlib import Path


class AITextureCleaner:
    """AI-powered texture cleaner using semantic segmentation to remove temporary elements"""
    
    # Classes to remove (temporary/transient objects)
    TRANSIENT_CLASSES = {
        'person', 'bicycle', 'car', 'motorcycle', 'bus', 
        'truck', 'traffic light', 'fire hydrant', 'stop sign',
        'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse',
        'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
        'backpack', 'umbrella', 'handbag', 'tie', 'suitcase'
    }
    
    # COCO class names for semantic segmentation
    COCO_CLASSES = [
        '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
        'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
        'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A',
        'N/A', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
        'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
        'surfboard', 'tennis racket', 'bottle', 'N/A', 'wine glass', 'cup', 'fork',
        'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'N/A', 'dining table', 'N/A', 'N/A', 'toilet', 'N/A',
        'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
        'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book', 'clock', 'vase',
        'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI texture cleaner
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.texture_config = config.get('texture_mapping', {})
        self.ai_config = self.texture_config.get('ai_cleaning', {})
        
        self.enabled = self.ai_config.get('enabled', True)
        self.model = None
        self.transforms = None
        
        if self.enabled:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.logger.info(f"AI Texture Cleaner using device: {self.device}")
            self._load_model()
        else:
            self.device = None
            self.logger.info("AI Texture Cleaner disabled")
    
    def _load_model(self):
        """Load pre-trained segmentation model"""
        try:
            from torchvision import models
            from torchvision.models.segmentation import DeepLabV3_MobileNet_V3_Large_Weights
            
            self.logger.info("Loading DeepLabV3 MobileNetV3 model for semantic segmentation...")
            
            # Use the latest recommended weights
            weights = DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT
            self.model = models.segmentation.deeplabv3_mobilenet_v3_large(
                weights=weights
            ).to(self.device)
            
            self.model.eval()
            self.transforms = weights.transforms()
            
            self.logger.info("AI segmentation model loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load AI model: {e}")
            self.logger.warning("Falling back to traditional CV methods")
            self.enabled = False
    
    def clean_image(self, image: np.ndarray) -> np.ndarray:
        """
        Clean image by detecting and removing temporary elements using AI
        
        Args:
            image: Input image (RGB format, numpy array)
            
        Returns:
            Cleaned image with temporary elements removed
        """
        if not self.enabled or self.model is None:
            self.logger.debug("AI cleaning disabled, returning original image")
            return image
        
        try:
            # Detect transient objects
            mask = self._detect_transient_objects(image)
            
            # Inpaint detected regions
            if np.any(mask > 0):
                cleaned = self._inpaint_regions(image, mask)
                self.logger.debug(f"AI cleaning removed transient objects from image")
                return cleaned
            else:
                return image
                
        except Exception as e:
            self.logger.warning(f"AI cleaning failed: {e}, returning original image")
            return image
    
    def _detect_transient_objects(self, image: np.ndarray) -> np.ndarray:
        """
        Detect transient objects (cars, people, etc.) in image using semantic segmentation
        
        Args:
            image: Input image (RGB)
            
        Returns:
            Binary mask of transient objects
        """
        # Prepare image for model
        if image.shape[2] == 3:
            # Convert RGB to PIL-like format for transforms
            from PIL import Image
            pil_image = Image.fromarray(image.astype('uint8'))
            input_tensor = self.transforms(pil_image).unsqueeze(0).to(self.device)
        else:
            self.logger.warning("Image must be RGB")
            return np.zeros(image.shape[:2], dtype=np.uint8)
        
        # Run inference
        with torch.no_grad():
            output = self.model(input_tensor)['out'][0]
            predictions = output.argmax(0).cpu().numpy()
        
        # Resize predictions to match original image size
        if predictions.shape != image.shape[:2]:
            predictions = cv2.resize(
                predictions.astype(np.uint8), 
                (image.shape[1], image.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )
        
        # Create mask for transient classes
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        for class_idx, class_name in enumerate(self.COCO_CLASSES):
            if class_name in self.TRANSIENT_CLASSES:
                mask[predictions == class_idx] = 255
        
        # Apply morphological operations to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Dilate slightly to ensure complete coverage
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.dilate(mask, kernel_dilate, iterations=1)
        
        return mask
    
    def _inpaint_regions(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Inpaint detected regions using advanced techniques
        
        Args:
            image: Input image
            mask: Binary mask of regions to inpaint
            
        Returns:
            Inpainted image
        """
        # Use Navier-Stokes based inpainting for better results
        # This method is better for larger regions than TELEA
        inpaint_radius = self.ai_config.get('inpaint_radius', 5)
        
        # Try Navier-Stokes first (better for complex structures)
        try:
            cleaned = cv2.inpaint(image, mask, inpaint_radius, cv2.INPAINT_NS)
        except:
            # Fall back to TELEA if NS fails
            cleaned = cv2.inpaint(image, mask, inpaint_radius, cv2.INPAINT_TELEA)
        
        return cleaned
    
    def batch_clean_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean multiple images in batch
        
        Args:
            images: List of image dictionaries with 'image' key
            
        Returns:
            List of cleaned image dictionaries
        """
        if not self.enabled:
            self.logger.info("AI cleaning disabled, returning original images")
            return images
        
        self.logger.info(f"AI cleaning {len(images)} images...")
        
        cleaned_images = []
        for i, img_data in enumerate(images):
            if 'image' not in img_data:
                self.logger.warning(f"Image {i} missing 'image' key, skipping")
                cleaned_images.append(img_data)
                continue
            
            img = img_data['image']
            cleaned_img = self.clean_image(img)
            
            cleaned_data = img_data.copy()
            cleaned_data['image'] = cleaned_img
            cleaned_images.append(cleaned_data)
            
            if (i + 1) % 10 == 0:
                self.logger.info(f"Processed {i + 1}/{len(images)} images")
        
        self.logger.info(f"AI cleaning completed for {len(cleaned_images)} images")
        return cleaned_images
    
    def get_statistics(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about transient objects detected in images
        
        Args:
            images: List of image dictionaries
            
        Returns:
            Dictionary with detection statistics
        """
        if not self.enabled:
            return {'enabled': False, 'message': 'AI cleaning disabled'}
        
        stats = {
            'enabled': True,
            'total_images': len(images),
            'images_with_transients': 0,
            'total_transient_pixels': 0,
            'avg_transient_percentage': 0.0,
            'classes_detected': set()
        }
        
        for img_data in images:
            if 'image' not in img_data:
                continue
            
            mask = self._detect_transient_objects(img_data['image'])
            transient_pixels = np.sum(mask > 0)
            
            if transient_pixels > 0:
                stats['images_with_transients'] += 1
                stats['total_transient_pixels'] += transient_pixels
        
        if stats['total_images'] > 0:
            total_pixels = sum(
                img_data['image'].shape[0] * img_data['image'].shape[1]
                for img_data in images if 'image' in img_data
            )
            if total_pixels > 0:
                stats['avg_transient_percentage'] = (
                    stats['total_transient_pixels'] / total_pixels * 100
                )
        
        return stats
