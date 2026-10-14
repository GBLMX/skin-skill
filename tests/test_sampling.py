"""Tests for reference-image color sampling."""

from PIL import Image

from skinlib.sampling import palette_of_image


def _img(colors, size=4):
    """A ``size`` x ``size`` RGBA image painted row by row from ``colors``."""
    im = Image.new("RGBA", (size, size))
    px = im.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = colors[(y * size + x) % len(colors)]
    return im


def test_palette_merges_near_identical_colors_by_default():
    # Three hand-drawn reds are one color to a noisy reference image.
    reds = _img([(200, 10, 10, 255), (206, 12, 11, 255), (199, 9, 9, 255)])
    assert palette_of_image(reds, 8) == [(192, 0, 0, 255)]


def test_palette_keeps_exact_colors_when_asked():
    # Binning would darken both of these; matching wants the real values.
    im = _img([(253, 251, 154, 255), (200, 205, 180, 255)])
    assert sorted(palette_of_image(im, 8, quantize=False)) == sorted(
        [(253, 251, 154, 255), (200, 205, 180, 255)])


def test_palette_respects_a_mask():
    im = _img([(200, 0, 0, 255), (0, 0, 200, 255)])
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((0, 0), 255)
    assert palette_of_image(im, 8, mask, quantize=False) == [(200, 0, 0, 255)]


def test_transparent_pixels_never_count():
    im = _img([(200, 0, 0, 255), (0, 0, 200, 0)])
    assert palette_of_image(im, 8, quantize=False) == [(200, 0, 0, 255)]
