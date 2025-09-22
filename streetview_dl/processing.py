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
        saturation: float = 1.0,
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
        """Apply a sepia tone using a color matrix that preserves tonal range.

        Uses the classic sepia transform:
            R' = 0.393R + 0.769G + 0.189B
            G' = 0.349R + 0.686G + 0.168B
            B' = 0.272R + 0.534G + 0.131B

        This keeps highlights and midtones intact and warms colors without
        compressing the histogram into two endpoints.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 3x4 matrix (flattened) for RGB output channels
        matrix = [
            0.393,
            0.769,
            0.189,
            0.0,  # R'
            0.349,
            0.686,
            0.168,
            0.0,  # G'
            0.272,
            0.534,
            0.131,
            0.0,  # B'
        ]

        sepia = image.convert("RGB", matrix)
        return sepia

    @staticmethod
    def _apply_vintage(image: Image.Image) -> Image.Image:
        """Apply vintage effect (sepia + adjustments)."""
        # Apply sepia first
        vintage = ImageProcessor._apply_sepia(image)

        # Reduce contrast and brightness slightly for vintage look
        vintage = ImageProcessor.adjust_image(
            vintage, brightness=0.95, contrast=0.85, saturation=0.8
        )

        return vintage

    @staticmethod
    def resize_if_larger(
        image: Image.Image, max_width: int, max_height: int = None
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
