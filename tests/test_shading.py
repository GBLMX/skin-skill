"""Tests for shading algorithms (gradient, cylinder, noise, dispatch)."""

import pytest

from skinlib import Skin, apply_shading
from skinlib.shading import cylindrical, vertical_gradient, fabric_noise


def _lum(c):
    return c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114


def test_flat_equals_base():
    s = Skin()
    base = (120, 20, 25, 255)
    apply_shading(s, "body", base, "base", style="flat")
    x, y, w, h = s.region("body", "base", "front")
    for i in range(w):
        for j in range(h):
            assert s.img.getpixel((x + i, y + j)) == base


def test_cylindrical_center_brighter_than_edge():
    s = Skin()
    cylindrical(s, "head", (100, 100, 100, 255), "base")
    x, y, w, h = s.region("head", "base", "front")
    edge = s.img.getpixel((x, y + h // 2))
    center = s.img.getpixel((x + w // 2, y + h // 2))
    assert _lum(center) > _lum(edge)


def test_vertical_top_brighter():
    s = Skin()
    vertical_gradient(s, "body", (255, 255, 255, 255), (0, 0, 0, 255), "base")
    x, y, w, h = s.region("body", "base", "front")
    top = s.img.getpixel((x + w // 2, y))
    bottom = s.img.getpixel((x + w // 2, y + h - 1))
    assert _lum(top) > _lum(bottom)


def test_fabric_noise_deterministic():
    base = (128, 128, 128, 255)
    s1 = Skin(); s1.paint_part("body", base, "base")
    s2 = Skin(); s2.paint_part("body", base, "base")
    fabric_noise(s1, "body", "base", variance=6, seed=42)
    fabric_noise(s2, "body", "base", variance=6, seed=42)
    assert s1.img.tobytes() == s2.img.tobytes()


def test_apply_shading_unknown_style():
    with pytest.raises(ValueError):
        apply_shading(Skin(), "body", (1, 2, 3, 255), "base", style="nope")
