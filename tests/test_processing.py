from PIL import Image

from streetview_dl.processing import ImageProcessor


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

