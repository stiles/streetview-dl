"""Image processing and filtering functionality."""

from PIL import Image, ImageEnhance, ImageOps
from typing import Tuple


class ImageProcessor:
    """Handle image processing and filtering operations."""
    
    @staticmethod
    def apply_filter(image: Image.Image, filter_type: str) -> Image.Image:
        """Apply artistic filters to the image."""
        if filter_type == "none":
            return image
        elif filter_type == "bw":
            return ImageOps.grayscale(image).convert("RGB")
        elif filter_type == "sepia":
            return ImageProcessor._apply_sepia(image)
        elif filter_type == "vintage":
            return ImageProcessor._apply_vintage(image)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
    
    @staticmethod
    def adjust_image(
        image: Image.Image, 
        brightness: float = 1.0, 
        contrast: float = 1.0, 
        saturation: float = 1.0
    ) -> Image.Image:
        """Adjust brightness, contrast, and saturation."""
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)
        
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(saturation)
        
        return image
    
    @staticmethod
    def _apply_sepia(image: Image.Image) -> Image.Image:
        """Apply sepia tone effect."""
        # Convert to grayscale first
        grayscale = ImageOps.grayscale(image)
        
        # Create sepia effect by colorizing
        sepia = ImageOps.colorize(grayscale, "#704214", "#C0A080")
        return sepia
    
    @staticmethod
    def _apply_vintage(image: Image.Image) -> Image.Image:
        """Apply vintage effect (sepia + adjustments)."""
        # Apply sepia first
        vintage = ImageProcessor._apply_sepia(image)
        
        # Reduce contrast and brightness slightly for vintage look
        vintage = ImageProcessor.adjust_image(
            vintage, 
            brightness=0.95, 
            contrast=0.85, 
            saturation=0.8
        )
        
        return vintage
    
    @staticmethod
    def resize_if_larger(
        image: Image.Image, 
        max_width: int, 
        max_height: int = None
    ) -> Tuple[Image.Image, bool]:
        """
        Resize image if it exceeds maximum dimensions.
        
        Returns:
            Tuple of (resized_image, was_resized)
        """
        width, height = image.size
        
        if width <= max_width and (max_height is None or height <= max_height):
            return image, False
        
        if max_height is None:
            # Maintain aspect ratio, scale by width
            scale = max_width / width
            new_height = int(height * scale)
            new_size = (max_width, new_height)
        else:
            # Scale to fit within both dimensions
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            new_size = (new_width, new_height)
        
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        return resized, True
