"""2D gradient-noise backends (Simplex via opensimplex, Perlin fallback).

Prefers `opensimplex` (Simplex noise) when it is installed; otherwise falls
back to a pure-Python Perlin implementation so the library keeps working
with zero dependencies beyond Pillow. Both backends are seeded, deterministic,
and normalized to [-1, 1] so callers can treat the output as a signed
brightness offset.
"""

from __future__ import annotations

import random

try:
    from opensimplex import OpenSimplex
    _HAS_SIMPLEX = True
except ImportError:  # pragma: no cover - exercised only without opensimplex
    OpenSimplex = None
    _HAS_SIMPLEX = False


class _Perlin:
    """Classic 2D Perlin gradient noise, normalized to [-1, 1]."""

    def __init__(self, seed: int = 0):
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self._perm = p + p  # doubled for wrap-around indexing

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    @staticmethod
    def _grad(hash_: int, x: float, y: float) -> float:
        h = hash_ & 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def noise2(self, x: float, y: float) -> float:
        """Sample 2D Perlin noise in [-1, 1]."""
        xi = int(x) & 255
        yi = int(y) & 255
        xf = x - int(x)
        yf = y - int(y)
        u = self._fade(xf)
        v = self._fade(yf)

        p = self._perm
        aa = p[p[xi] + yi]
        ab = p[p[xi] + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]

        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)


class Noise2D:
    """A seeded 2D noise source normalized to [-1, 1].

    Uses opensimplex (Simplex) when available, otherwise the built-in Perlin
    implementation. ``backend`` reports which is active.
    """

    def __init__(self, seed: int = 0):
        if _HAS_SIMPLEX:
            self._fn = OpenSimplex(seed).noise2
            self.backend = "simplex"
        else:
            self._fn = _Perlin(seed).noise2
            self.backend = "perlin"

    def noise2(self, x: float, y: float) -> float:
        return self._fn(x, y)
