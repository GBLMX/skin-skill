"""Tests for the observed artistic lighting style."""

from skinlib import Skin
from skinlib.artistic import artistic


def _lum(c):
    return c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114


def test_artistic_top_brighter_than_bottom():
    s = Skin()
    base = (150, 120, 100, 255)
    artistic(s, "body", base, "base")
    x, y, w, h = s.region("body", "base", "front")
    mid = x + w // 2
    top = s.img.getpixel((mid, y))
    bottom = s.img.getpixel((mid, y + h - 1))
    assert _lum(top) > _lum(bottom)


def test_artistic_folds_change_pixels():
    base = (150, 120, 100, 255)
    s1 = Skin(); artistic(s1, "body", base, "base", folds=True)
    s2 = Skin(); artistic(s2, "body", base, "base", folds=False)
    assert s1.img.tobytes() != s2.img.tobytes()


def test_artistic_deterministic():
    base = (150, 120, 100, 255)
    s1 = Skin(); artistic(s1, "body", base, "base")
    s2 = Skin(); artistic(s2, "body", base, "base")
    assert s1.img.tobytes() == s2.img.tobytes()
