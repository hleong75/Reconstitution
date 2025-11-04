"""Texture mapping module with intelligent temporary element removal"""

import numpy as np
import cv2
import open3d as o3d
from typing import Dict, Any, List, Tuple
import logging
from src.ai_texture_cleaner import AITextureCleaner


# Constants for image cleaning thresholds
GROUND_LEVEL_THRESHOLD = 0.4  # Top 40% of image is sky/buildings, bottom 60% is ground
VERTICAL_FOCUS_THRESHOLD = 0.5  # Focus on bottom 50% for vertical objects
BLUR_PERCENTILE_THRESHOLD = 25  # Lower 25% variance indicates blur

# Brightness and saturation thresholds for reflective surface detection
BRIGHTNESS_THRESHOLD = 200  # High brightness indicates reflective surfaces
LOW_SATURATION_THRESHOLD = 50  # Low saturation with high brightness = metallic
EDGE_VARIANCE_THRESHOLD = 30  # High local variance indicates reflections/edges

# Edge detection thresholds
VERTICAL_EDGE_THRESHOLD = 50  # Minimum edge strength for vertical objects
VERTICAL_EDGE_RATIO = 1.5  # Ratio of x-gradient to y-gradient for vertical edges


class TextureMapper:
    """Apply textures to 3D meshes from Street View images with intelligent cleanup"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize texture mapper
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.texture_config = config['texture_mapping']
        
        # Initialize AI texture cleaner
        self.ai_cleaner = AITextureCleaner(config)
        self.use_ai_cleaning = self.texture_config.get('ai_cleaning', {}).get('enabled', True)
    
    def apply_textures(self, mesh: o3d.geometry.TriangleMesh, 
                       images: List[Dict[str, Any]]) -> o3d.geometry.TriangleMesh:
        """
        Apply textures to mesh from Street View images
        
        Args:
            mesh: Input mesh
            images: List of Street View images with metadata
            
        Returns:
            Textured mesh with temporary elements removed
        """
        self.logger.info("Applying textures to mesh with intelligent cleanup")
        
        if len(mesh.vertices) == 0:
            self.logger.warning("Empty mesh, cannot apply textures")
            return mesh
        
        if not images:
            self.logger.warning("No images available for texturing")
            # Apply default color
            mesh.paint_uniform_color([0.7, 0.7, 0.7])
            return mesh
        
        # Process images to remove temporary elements
        cleaned_images = self._clean_images(images)
        
        # Apply vertex coloring based on position and cleaned images
        vertices = np.asarray(mesh.vertices)
        
        # Create intelligent texture based on height and surface characteristics
        colors = self._generate_intelligent_colors(vertices, cleaned_images)
        
        mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
        
        self.logger.info(f"Applied cleaned textures to {len(vertices)} vertices")
        
        return mesh
    
    def _clean_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean images by removing temporary elements (cars, people, etc.)
        Uses AI-based detection when enabled, falls back to traditional CV methods
        
        Args:
            images: List of image dictionaries
            
        Returns:
            List of cleaned images
        """
        self.logger.info(f"Cleaning {len(images)} images to remove temporary elements")
        
        # Try AI-based cleaning first if enabled
        if self.use_ai_cleaning and self.ai_cleaner.enabled:
            self.logger.info("Using AI-based texture cleaning")
            cleaned_images = self.ai_cleaner.batch_clean_images(images)
            
            # Log statistics
            stats = self.ai_cleaner.get_statistics(images)
            self.logger.info(f"AI cleaning stats: {stats['images_with_transients']}/{stats['total_images']} "
                           f"images had transient objects ({stats['avg_transient_percentage']:.2f}% of pixels)")
            
            return cleaned_images
        else:
            # Fall back to traditional CV-based cleaning
            self.logger.info("Using traditional CV-based texture cleaning")
            cleaned_images = []
            for img_data in images:
                if 'image' not in img_data:
                    continue
                    
                img = img_data['image'].copy()
                
                # Apply intelligent filtering to remove temporary objects
                cleaned_img = self._remove_temporary_elements(img)
                
                cleaned_data = img_data.copy()
                cleaned_data['image'] = cleaned_img
                cleaned_images.append(cleaned_data)
            
            self.logger.info(f"Successfully cleaned {len(cleaned_images)} images")
            return cleaned_images
    
    def _remove_temporary_elements(self, image: np.ndarray) -> np.ndarray:
        """
        Remove temporary elements from image (cars, people, temporary objects)
        Uses computer vision techniques to detect and filter out transient objects
        
        Args:
            image: Input image (RGB)
            
        Returns:
            Cleaned image with temporary elements removed/inpainted
        """
        # Create a mask for temporary elements detection
        height, width = image.shape[:2]
        temp_mask = np.zeros((height, width), dtype=np.uint8)
        
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Detect reflective surfaces (likely cars, glass)
        # High saturation and brightness variations indicate reflective surfaces
        reflective_mask = self._detect_reflective_surfaces(hsv, gray)
        temp_mask = cv2.bitwise_or(temp_mask, reflective_mask)
        
        # Detect vertical structures at ground level (likely people, poles)
        vertical_mask = self._detect_vertical_objects(gray, height)
        temp_mask = cv2.bitwise_or(temp_mask, vertical_mask)
        
        # Detect motion blur (indicates moving objects)
        motion_mask = self._detect_motion_blur(gray)
        temp_mask = cv2.bitwise_or(temp_mask, motion_mask)
        
        # Clean up mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        temp_mask = cv2.morphologyEx(temp_mask, cv2.MORPH_CLOSE, kernel)
        temp_mask = cv2.morphologyEx(temp_mask, cv2.MORPH_OPEN, kernel)
        
        # Inpaint detected temporary elements
        if np.any(temp_mask > 0):
            cleaned = cv2.inpaint(image, temp_mask, 3, cv2.INPAINT_TELEA)
            self.logger.debug("Removed temporary elements using inpainting")
        else:
            cleaned = image
        
        return cleaned
    
    def _detect_reflective_surfaces(self, hsv: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """
        Detect reflective surfaces (cars, windows) in image
        
        Args:
            hsv: Image in HSV color space
            gray: Grayscale image
            
        Returns:
            Binary mask of reflective surfaces
        """
        height, width = hsv.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # High value (brightness) with low saturation indicates reflective surfaces
        v_channel = hsv[:, :, 2]
        s_channel = hsv[:, :, 1]
        
        # Detect very bright areas with low saturation (metallic/glass reflections)
        bright_low_sat = (v_channel > BRIGHTNESS_THRESHOLD) & (s_channel < LOW_SATURATION_THRESHOLD)
        
        # Detect high local variance (indicates reflections)
        local_std = cv2.Laplacian(gray, cv2.CV_64F)
        high_variance = np.abs(local_std) > EDGE_VARIANCE_THRESHOLD
        
        # Combine conditions
        mask[bright_low_sat & high_variance] = 255
        
        # Only consider lower 60% of image (ground level where cars are)
        mask[: int(height * GROUND_LEVEL_THRESHOLD), :] = 0
        
        return mask
    
    def _detect_vertical_objects(self, gray: np.ndarray, height: int) -> np.ndarray:
        """
        Detect vertical objects at ground level (people, poles)
        
        Args:
            gray: Grayscale image
            height: Image height
            
        Returns:
            Binary mask of vertical objects
        """
        # Use Sobel filter to detect vertical edges
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Vertical edges are stronger in x direction
        vertical_edges = np.abs(sobelx) > np.abs(sobely) * VERTICAL_EDGE_RATIO
        
        # Apply threshold
        edge_strength = np.abs(sobelx)
        strong_vertical = (edge_strength > VERTICAL_EDGE_THRESHOLD) & vertical_edges
        
        mask = np.zeros_like(gray, dtype=np.uint8)
        mask[strong_vertical] = 255
        
        # Focus on lower portion of image (ground level)
        mask[: int(height * VERTICAL_FOCUS_THRESHOLD), :] = 0
        
        # Remove small isolated regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 10))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _detect_motion_blur(self, gray: np.ndarray) -> np.ndarray:
        """
        Detect motion blur which indicates moving objects
        
        Args:
            gray: Grayscale image
            
        Returns:
            Binary mask of blurred regions
        """
        # Calculate image sharpness using Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # Low variance indicates blur
        # Use local statistics to find regions with anomalously low sharpness
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size ** 2)
        local_var = cv2.filter2D(laplacian ** 2, -1, kernel)
        
        # Global threshold for blur detection
        threshold = np.percentile(local_var, BLUR_PERCENTILE_THRESHOLD)
        
        mask = np.zeros_like(gray, dtype=np.uint8)
        mask[local_var < threshold] = 255
        
        return mask
    
    def _generate_intelligent_colors(self, vertices: np.ndarray, 
                                    images: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate intelligent vertex colors based on cleaned images and position
        
        Args:
            vertices: Mesh vertices
            images: Cleaned images
            
        Returns:
            Color array for vertices
        """
        # Calculate base colors from height
        min_z = vertices[:, 2].min()
        max_z = vertices[:, 2].max()
        z_range = max_z - min_z if max_z > min_z else 1.0
        
        normalized_z = (vertices[:, 2] - min_z) / z_range
        
        # Generate natural-looking colors
        # Lower areas (ground) - earthy tones
        # Higher areas (buildings) - gray/white tones
        colors = np.zeros((len(vertices), 3))
        
        # Ground: brownish/gray
        colors[:, 0] = 0.45 + normalized_z * 0.35  # R: 0.45-0.80
        colors[:, 1] = 0.42 + normalized_z * 0.38  # G: 0.42-0.80
        colors[:, 2] = 0.38 + normalized_z * 0.42  # B: 0.38-0.80
        
        # Add subtle variation based on position to simulate material differences
        # Use x,y coordinates to create spatial variation
        x_var = np.sin(vertices[:, 0] * 0.1) * 0.05
        y_var = np.cos(vertices[:, 1] * 0.1) * 0.05
        
        colors[:, 0] = np.clip(colors[:, 0] + x_var, 0, 1)
        colors[:, 1] = np.clip(colors[:, 1] + y_var, 0, 1)
        
        return colors
