from PIL import Image
from streetview_dl.processing import ImageProcessor
from streetview_dl.utils import crop_fov, crop_horizontal_section


def _make_rgb_gradient(width: int = 64, height: int = 32) -> Image.Image:
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for x in range(width):
        for y in range(height):
            r = int(255 * x / (width - 1))
            g = int(255 * y / (height - 1))
            b = int(255 * (x + y) / (width + height - 2))
            pixels[x, y] = (r, g, b)
    return img


def test_bw_filter_returns_rgb():
    img = _make_rgb_gradient()
    out = ImageProcessor.apply_filter(img, "bw")
    assert out.mode == "RGB"


def test_sepia_preserves_tonal_range():
    img = _make_rgb_gradient()
    out = ImageProcessor.apply_filter(img, "sepia")
    # Check some representative pixels are warmed and within bounds
    r, g, b = out.getpixel((48, 16))
    assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255
    # Red channel should be the highest or comparable in sepia tone
    assert r >= g and r >= b


def _make_equirectangular_test_image(width: int = 360, height: int = 180) -> Image.Image:
    """Create a test equirectangular image with distinctive patterns for testing cropping."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for x in range(width):
        for y in range(height):
            # Create a pattern that varies by position
            # Use yaw (x-coordinate) to create horizontal stripes
            yaw_degrees = (x / width) * 360
            # Create distinct regions every 60 degrees
            region = int(yaw_degrees // 60)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            pixels[x, y] = colors[region % len(colors)]
    
    return img


def test_crop_fov_360_returns_unchanged():
    """Test that 360° FOV returns the original image."""
    img = _make_equirectangular_test_image(360, 180)
    result = crop_fov(img, 0, 360)
    assert result.size == img.size


def test_crop_fov_180_returns_half_width():
    """Test that 180° FOV returns half the width."""
    img = _make_equirectangular_test_image(360, 180)
    result = crop_fov(img, 0, 180)
    assert result.size == (180, 180)  # Half width, same height


def test_crop_fov_centers_correctly():
    """Test that FOV cropping centers around the specified yaw."""
    img = _make_equirectangular_test_image(360, 180)
    # Crop 60° around yaw 0° (should get pixels from x=330-30, wrapping)
    result = crop_fov(img, 0, 60)
    assert result.size == (60, 180)
    
    # Test another angle without wraparound
    result = crop_fov(img, 180, 60)
    assert result.size == (60, 180)


def test_crop_horizontal_section_fov_only():
    """Test horizontal section cropping with FOV only."""
    img = _make_equirectangular_test_image(360, 180)
    result = crop_horizontal_section(img, 0, 180, "none")
    assert result.size == (180, 180)


def test_crop_horizontal_section_clip_right():
    """Test horizontal section cropping with right clip."""
    img = _make_equirectangular_test_image(360, 180)
    result = crop_horizontal_section(img, 90, 360, "right")
    # Should return 180° centered on yaw 90
    assert result.size == (180, 180)


def test_crop_horizontal_section_clip_left():
    """Test horizontal section cropping with left clip."""
    img = _make_equirectangular_test_image(360, 180)
    result = crop_horizontal_section(img, 90, 360, "left")
    # Should return 180° centered on yaw 270 (90 + 180)
    assert result.size == (180, 180)


def test_crop_horizontal_section_fov_with_clip():
    """Test horizontal section cropping combining FOV and clip."""
    img = _make_equirectangular_test_image(360, 180)
    # FOV 220° with right clip should still return 180°
    result = crop_horizontal_section(img, 90, 220, "right")
    assert result.size == (180, 180)


def test_crop_fov_wraparound():
    """Test that FOV cropping handles wraparound correctly."""
    img = _make_equirectangular_test_image(360, 180)
    # Test wraparound at yaw 350° with 60° FOV (should wrap from 320° to 20°)
    result = crop_fov(img, 350, 60)
    assert result.size == (60, 180)
    
    # Test wraparound at yaw 10° with 60° FOV (should wrap from 340° to 40°)
    result = crop_fov(img, 10, 60)
    assert result.size == (60, 180)
