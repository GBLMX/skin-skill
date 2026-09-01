"""Tests for pure color math."""

from skinlib import mix, shade, gray, blend, gradient
from skinlib.colors import palette


def test_mix_endpoints_and_clamp():
    assert mix((0, 0, 0, 255), (255, 255, 255, 255), 0.0) == (0, 0, 0, 255)
    assert mix((0, 0, 0, 255), (255, 255, 255, 255), 1.0) == (255, 255, 255, 255)
    assert mix((0, 0, 0, 255), (100, 100, 100, 255), 0.5) == (50, 50, 50, 255)
    # out-of-range t is clamped
    assert mix((0, 0, 0, 255), (255, 255, 255, 255), 5.0) == (255, 255, 255, 255)


def test_shade():
    assert shade((100, 100, 100, 255), 0.5) == (50, 50, 50, 255)
    assert shade((100, 100, 100, 255), 2.0) == (200, 200, 200, 255)
    assert shade((255, 255, 255, 128), 3.0) == (255, 255, 255, 128)  # clamp + alpha kept


def test_gray():
    assert gray((255, 0, 0, 255))[:3] == (76, 76, 76)  # 0.299 * 255


def test_blend():
    assert blend((10, 20, 30, 255), (0, 0, 0, 0)) == (10, 20, 30, 255)
    assert blend((0, 0, 0, 0), (10, 20, 30, 255)) == (10, 20, 30, 255)


def test_gradient():
    g = gradient((0, 0, 0, 255), (255, 255, 255, 255), 3)
    assert g == [(0, 0, 0, 255), (128, 128, 128, 255), (255, 255, 255, 255)]


def test_palette_two_segments():
    p = palette((0, 0, 0, 255), (255, 255, 255, 255), (0, 0, 0, 255), 3)
    assert p[0] == (0, 0, 0, 255)
    assert p[-1] == (0, 0, 0, 255)
