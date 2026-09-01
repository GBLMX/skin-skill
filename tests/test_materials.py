"""Tests for the material system."""

import pytest

from skinlib import Skin, MATERIALS, apply_material


def _lum(c):
    return c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114


def test_materials_registry():
    assert set(MATERIALS) == {"cloth", "leather", "metal", "bone", "glow_crystal"}


def test_apply_material_paints_part():
    s = Skin()
    apply_material(s, "body", "leather")
    x, y, w, h = s.region("body", "base", "front")
    opaque = sum(1 for i in range(w) for j in range(h)
                 if s.img.getpixel((x + i, y + j))[3] > 0)
    assert opaque == w * h


def test_all_materials_apply():
    for name in MATERIALS:
        s = Skin()
        apply_material(s, "head", name)
        apply_material(s, "body", name, color=(100, 100, 100, 255))


def test_deterministic():
    s1 = Skin(); apply_material(s1, "body", "metal", seed=7)
    s2 = Skin(); apply_material(s2, "body", "metal", seed=7)
    assert s1.img.tobytes() == s2.img.tobytes()


def test_metal_specular_center_brighter():
    s = Skin()
    apply_material(s, "head", "metal")
    x, y, w, h = s.region("head", "base", "front")
    center = s.img.getpixel((x + w // 2, y + h // 2))
    off = s.img.getpixel((x + w // 2 + 2, y + h // 2))
    assert _lum(center) > _lum(off)


def test_glow_crystal_center_bright():
    s = Skin()
    apply_material(s, "head", "glow_crystal")
    x, y, w, h = s.region("head", "base", "front")
    center = s.img.getpixel((x + w // 2, y + h // 2))
    corner = s.img.getpixel((x, y))
    assert _lum(center) > _lum(corner)


def test_unknown_material():
    with pytest.raises(ValueError):
        apply_material(Skin(), "body", "nope")
