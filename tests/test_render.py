"""Tests for the preview renderers (flat, isometric, 3D)."""

import pytest
from PIL import Image

from skinlib import PARTS, Skin, render_3d, render_flat, render_isometric


def _painted(model="steve", size=64):
    """Fresh skin with every part's base layer painted opaque."""
    s = Skin(size=size, model=model)
    for i, part in enumerate(PARTS):
        s.paint_part(part, (20 + i * 35, 90, 160, 255))
    return s


def test_render_flat_scales_canvas():
    s = _painted()
    img = render_flat(s, scale=4)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA"
    assert img.size == (256, 256)
    big = render_flat(s, scale=8)
    assert big.size == (512, 512)  # scale enlarges the output


def test_render_flat_deterministic():
    s = _painted()
    assert render_flat(s).tobytes() == render_flat(s).tobytes()


def test_render_flat_painted_skin_has_opaque_pixels():
    s = _painted()
    assert any(p[3] > 0 for p in render_flat(s, scale=2).getdata())


def test_render_isometric_front_and_back():
    s = _painted()
    for view in ("front", "back"):
        img = render_isometric(s, view=view)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"
        assert img.size == (320, 400)


def test_render_isometric_deterministic():
    s = _painted()
    assert render_isometric(s).tobytes() == render_isometric(s).tobytes()


def test_render_3d_canvas():
    s = _painted()
    img = render_3d(s)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA"
    assert img.size == (400, 500)


def test_render_3d_scale_keeps_canvas_size():
    # render_3d's `scale` magnifies the projected body inside a fixed canvas.
    s = _painted()
    small = render_3d(s, scale=4)
    large = render_3d(s, scale=16)
    assert small.size == large.size == (400, 500)


def test_render_3d_deterministic():
    s = _painted()
    assert render_3d(s).tobytes() == render_3d(s).tobytes()


@pytest.mark.parametrize(
    "model,size", [("steve", 64), ("alex", 64), ("steve", 128), ("alex", 128)]
)
def test_renderers_support_every_skin(model, size):
    s = _painted(model=model, size=size)
    for img in (render_flat(s), render_isometric(s), render_3d(s)):
        assert img.mode == "RGBA"
    # flat enlarges the texture sheet; canvas renderers keep their size
    assert render_flat(s).size == (size * 4, size * 4)
    assert render_isometric(s).size == (320, 400)
    assert render_3d(s).size == (400, 500)
