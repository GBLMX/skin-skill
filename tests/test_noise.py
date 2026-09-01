"""Tests for the noise backends and grain pass."""

from skinlib import Skin, noise_grain
from skinlib._noise import Noise2D


def test_noise2d_deterministic():
    a = Noise2D(seed=3)
    b = Noise2D(seed=3)
    for i in range(10):
        for j in range(10):
            assert a.noise2(i * 0.1, j * 0.1) == b.noise2(i * 0.1, j * 0.1)


def test_noise2d_range():
    n = Noise2D(seed=1)
    vals = [n.noise2(i * 0.7, j * 0.3) for i in range(20) for j in range(20)]
    assert all(-1.0 <= v <= 1.0 for v in vals)


def test_noise_grain_deterministic():
    base = (128, 128, 128, 255)
    s1 = Skin(); s1.paint_part("body", base, "base")
    s2 = Skin(); s2.paint_part("body", base, "base")
    noise_grain(s1, "body", "base", variance=8, seed=11)
    noise_grain(s2, "body", "base", variance=8, seed=11)
    assert s1.img.tobytes() == s2.img.tobytes()


def test_noise_grain_returns_skin_for_chaining():
    s = Skin()
    s.paint_part("body", (128, 128, 128, 255), "base")
    assert noise_grain(s, "body", "base", seed=0) is s
