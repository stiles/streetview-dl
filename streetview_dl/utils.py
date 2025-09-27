"""Utility functions for streetview-dl."""

from pathlib import Path
from PIL import Image


def write_xmp_metadata(image_path: str, image: Image.Image) -> None:
    """
    Embed XMP metadata to mark image as 360° panorama.

    This adds PhotoSphere metadata so the image is recognized as a 360° panorama
    by viewers that support spherical images.
    """
    # Create minimal XMP metadata for 360° panorama
    xmp_data = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description xmlns:GPano="http://ns.google.com/photos/1.0/panorama/" '
        'GPano:ProjectionType="equirectangular" '
        f'GPano:FullPanoWidthPixels="{image.width}" '
        f'GPano:FullPanoHeightPixels="{image.height}" '
        'GPano:CroppedAreaLeftPixels="0" '
        'GPano:CroppedAreaTopPixels="0" '
        f'GPano:CroppedAreaImageWidthPixels="{image.width}" '
        f'GPano:CroppedAreaImageHeightPixels="{image.height}" />'
        "</rdf:RDF>"
        "</x:xmpmeta>"
    ).encode("utf-8")

    # Read the existing JPEG file
    with open(image_path, "rb") as f:
        jpeg_data = f.read()

    # Find where to insert XMP (after existing APP1 segments if any)
    insert_pos = 2  # After SOI marker

    # Look for existing APP1 segments and insert after them
    pos = 2
    while pos < len(jpeg_data) - 1:
        if jpeg_data[pos : pos + 2] == b"\xff\xe1":  # APP1 marker
            # Skip this APP1 segment
            segment_length = (jpeg_data[pos + 2] << 8) | jpeg_data[pos + 3]
            pos += 2 + segment_length
            insert_pos = pos
        elif jpeg_data[pos : pos + 2] in [
            b"\xff\xe0",
            b"\xff\xfe",
        ]:  # APP0 or COM
            # Skip this segment
            segment_length = (jpeg_data[pos + 2] << 8) | jpeg_data[pos + 3]
            pos += 2 + segment_length
            insert_pos = pos
        else:
            break

    # Create the XMP APP1 segment
    xmp_namespace = b"http://ns.adobe.com/xap/1.0/\x00"
    xmp_payload = xmp_namespace + xmp_data
    xmp_length = len(xmp_payload) + 2  # +2 for the length field itself

    xmp_segment = (
        b"\xff\xe1"  # APP1 marker
        + xmp_length.to_bytes(2, "big")  # Segment length
        + xmp_payload
    )

    # Write the modified JPEG
    with open(image_path, "wb") as f:
        f.write(jpeg_data[:insert_pos])
        f.write(xmp_segment)
        f.write(jpeg_data[insert_pos:])


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_output_path(path: str, create_dirs: bool = True) -> Path:
    """
    Validate and prepare output path.

    Args:
        path: Output file path
        create_dirs: Whether to create parent directories

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid
    """
    output_path = Path(path)

    if create_dirs:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if we can write to the directory
    if not output_path.parent.exists():
        raise ValueError(
            f"Output directory does not exist: {output_path.parent}"
        )

    if not output_path.parent.is_dir():
        raise ValueError(
            f"Output path parent is not a directory: {output_path.parent}"
        )

    return output_path


def safe_filename(text: str, max_length: int = 255) -> str:
    """
    Create a safe filename from text.

    Removes or replaces characters that aren't safe for filenames.
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        text = text.replace(char, "_")

    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32)

    # Trim length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove leading/trailing spaces and dots
    text = text.strip(" .")

    return text or "streetview"


def crop_fov(
    image: Image.Image, center_yaw: float, fov_degrees: int
) -> Image.Image:
    """
    Crop an equirectangular panorama to show only a specific field of view.

    Args:
        image: Full equirectangular panorama image
        center_yaw: Yaw angle in degrees (0-360) for the center of the view
        fov_degrees: Field of view in degrees (60-360)

    Returns:
        Cropped image showing the specified field of view
    """
    width, height = image.size

    # Normalize yaw to 0-360 range
    center_yaw = center_yaw % 360

    # Calculate the horizontal crop boundaries
    # In equirectangular, yaw 0° is at the center (width/2)
    # Convert yaw to pixel position: yaw 0° = center, yaw 180° = edges
    center_x = (center_yaw / 360.0) * width

    # Calculate half the field of view in pixels
    half_fov_pixels = (fov_degrees / 360.0) * width / 2

    # Calculate crop boundaries
    left = int(center_x - half_fov_pixels)
    right = int(center_x + half_fov_pixels)

    # Handle wraparound for panoramas
    if fov_degrees >= 360:
        # No cropping needed for full 360°
        return image
    elif left < 0 or right > width:
        # Need to handle wraparound
        if left < 0:
            # Crop from right side + left side
            left_part = image.crop((width + left, 0, width, height))
            right_part = image.crop((0, right, width, height))
            # Concatenate the parts
            cropped = Image.new("RGB", (int(half_fov_pixels * 2), height))
            cropped.paste(left_part, (0, 0))
            cropped.paste(right_part, (left_part.width, 0))
            return cropped
        else:
            # right > width, crop from left side + right side
            left_part = image.crop((left, 0, width, height))
            right_part = image.crop((0, 0, right - width, height))
            cropped = Image.new("RGB", (int(half_fov_pixels * 2), height))
            cropped.paste(left_part, (0, 0))
            cropped.paste(right_part, (left_part.width, 0))
            return cropped
    else:
        # Simple crop, no wraparound needed
        return image.crop((left, 0, right, height))


def crop_horizontal_section(
    image: Image.Image, 
    center_yaw: float, 
    fov_degrees: int, 
    clip_direction: str = "none"
) -> Image.Image:
    """
    Crop an equirectangular panorama horizontally with unified coordinate system.
    
    Args:
        image: Full equirectangular panorama image
        center_yaw: Yaw angle in degrees (0-360) for the center of the view
        fov_degrees: Field of view in degrees (60-360)
        clip_direction: "none", "left", or "right" - clips to half relative to center_yaw
        
    Returns:
        Cropped image showing the specified section
    """
    width, height = image.size
    
    # Normalize yaw to 0-360 range
    center_yaw = center_yaw % 360
    
    # Adjust FOV based on clip direction
    if clip_direction in ("left", "right"):
        # Force FOV to 180° for directional clipping
        effective_fov = 180
        if clip_direction == "left":
            # Left = opposite direction (add 180°)
            center_yaw = (center_yaw + 180) % 360
    else:
        effective_fov = fov_degrees
    
    # Handle full 360° case
    if effective_fov >= 360:
        return image
        
    # Calculate the horizontal crop boundaries using consistent coordinate system
    # In equirectangular: yaw maps linearly to x-coordinate
    center_x = (center_yaw / 360.0) * width
    
    # Calculate half the field of view in pixels
    half_fov_pixels = (effective_fov / 360.0) * width / 2
    
    # Calculate crop boundaries
    left = center_x - half_fov_pixels
    right = center_x + half_fov_pixels
    
    # Handle wraparound for panoramas
    if left < 0 or right > width:
        # Need to handle wraparound - create new image by combining parts
        target_width = int(half_fov_pixels * 2)
        cropped = Image.new("RGB", (target_width, height))
        
        # Normalize coordinates
        left_mod = int(left % width)
        right_mod = int(right % width)
        
        if left < 0:
            # Left boundary wraps around
            left_part_width = width - left_mod
            right_part_width = int(right)
            
            # Get left part (from right side of image)
            left_part = image.crop((left_mod, 0, width, height))
            cropped.paste(left_part, (0, 0))
            
            # Get right part (from left side of image)  
            if right_part_width > 0:
                right_part = image.crop((0, 0, right_part_width, height))
                cropped.paste(right_part, (left_part_width, 0))
                
        else:
            # Right boundary wraps around
            left_part_width = width - int(left)
            
            # Get left part
            left_part = image.crop((int(left), 0, width, height))
            cropped.paste(left_part, (0, 0))
            
            # Get right part (wrapped)
            if right_mod > 0:
                right_part = image.crop((0, 0, right_mod, height))
                cropped.paste(right_part, (left_part_width, 0))
                
        return cropped
    else:
        # Simple crop, no wraparound needed
        return image.crop((int(left), 0, int(right), height))


def crop_bottom_fraction(
    image: Image.Image, keep_fraction: float
) -> Image.Image:
    """Crop bottom of image, keeping the top fraction of the height.

    Args:
        image: Source image
        keep_fraction: Fraction of height to keep from the top (0.0-1.0)

    Returns:
        Cropped image
    """
    keep_fraction = max(0.0, min(1.0, float(keep_fraction)))
    if keep_fraction >= 1.0:
        return image
    width, height = image.size
    new_height = max(1, int(height * keep_fraction))
    return image.crop((0, 0, width, new_height))
