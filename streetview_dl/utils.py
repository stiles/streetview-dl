"""Utility functions for streetview-dl."""

from pathlib import Path
from PIL import Image


def write_xmp_metadata(image_path: str, image: Image.Image) -> None:
    """
    Embed XMP metadata to mark image as 360° panorama.
    
    This adds PhotoSphere metadata so the image is recognized as a 360° panorama
    by viewers like Facebook, Google Photos, VR applications, etc.
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
        '</rdf:RDF>'
        '</x:xmpmeta>'
    ).encode("utf-8")
    
    # Read the existing JPEG file
    with open(image_path, "rb") as f:
        jpeg_data = f.read()
    
    # Find where to insert XMP (after existing APP1 segments if any)
    insert_pos = 2  # After SOI marker
    
    # Look for existing APP1 segments and insert after them
    pos = 2
    while pos < len(jpeg_data) - 1:
        if jpeg_data[pos:pos+2] == b"\xff\xe1":  # APP1 marker
            # Skip this APP1 segment
            segment_length = (jpeg_data[pos+2] << 8) | jpeg_data[pos+3]
            pos += 2 + segment_length
            insert_pos = pos
        elif jpeg_data[pos:pos+2] in [b"\xff\xe0", b"\xff\xfe"]:  # APP0 or COM
            # Skip this segment
            segment_length = (jpeg_data[pos+2] << 8) | jpeg_data[pos+3]
            pos += 2 + segment_length
            insert_pos = pos
        else:
            break
    
    # Create the XMP APP1 segment
    xmp_namespace = b"http://ns.adobe.com/xap/1.0/\x00"
    xmp_payload = xmp_namespace + xmp_data
    xmp_length = len(xmp_payload) + 2  # +2 for the length field itself
    
    xmp_segment = (
        b"\xff\xe1" +  # APP1 marker
        xmp_length.to_bytes(2, "big") +  # Segment length
        xmp_payload
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
        raise ValueError(f"Output directory does not exist: {output_path.parent}")
    
    if not output_path.parent.is_dir():
        raise ValueError(f"Output path parent is not a directory: {output_path.parent}")
    
    return output_path


def safe_filename(text: str, max_length: int = 255) -> str:
    """
    Create a safe filename from text.
    
    Removes or replaces characters that aren't safe for filenames.
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        text = text.replace(char, '_')
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    # Trim length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove leading/trailing spaces and dots
    text = text.strip(' .')
    
    return text or "streetview"
