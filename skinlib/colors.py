"""Color utilities for Minecraft skins (pure functions, no state)."""

from __future__ import annotations

from typing import Iterable, List, Tuple

Color = Tuple[int, int, int, int]


def _clamp(v: float) -> int:
    return max(0, min(255, round(v)))


def mix(c1: Color, c2: Color, t: float) -> Color:
    """Linear interpolation between two RGBA colors (t in [0,1])."""
    t = max(0.0, min(1.0, t))
    return tuple(_clamp(a + (b - a) * t) for a, b in zip(c1, c2))


def shade(color: Color, factor: float) -> Color:
    """Scale RGB by factor (darken <1, lighten >1); alpha unchanged."""
    r, g, b, a = color
    return (_clamp(r * factor), _clamp(g * factor), _clamp(b * factor), a)


def gray(color: Color) -> Color:
    """Luminance-based grayscale, alpha unchanged."""
    r, g, b, a = color
    v = _clamp(0.299 * r + 0.587 * g + 0.114 * b)
    return (v, v, v, a)


def blend(src: Color, dst: Color) -> Color:
    """Alpha-composite src over dst (both RGBA)."""
    sa = src[3] / 255.0
    da = dst[3] / 255.0
    out_a = sa + da * (1 - sa)
    if out_a == 0:
        return (0, 0, 0, 0)
    out = tuple(_clamp((sc * sa + dc * da * (1 - sa)) / out_a)
                for sc, dc in zip(src[:3], dst[:3]))
    return (*out, _clamp(out_a * 255))


def gradient(c1: Color, c2: Color, steps: int) -> List[Color]:
    """Return `steps` colors interpolating c1 -> c2 (inclusive)."""
    if steps <= 1:
        return [c1]
    return [mix(c1, c2, i / (steps - 1)) for i in range(steps)]


def palette(c1: Color, c2: Color, c3: Color, steps: int) -> List[Color]:
    """Two-segment gradient c1 -> c2 -> c3."""
    half = steps // 2
    return gradient(c1, c2, half + 1)[:-1] + gradient(c2, c3, steps - half)


def quantize(colors: Iterable[Color], n: int = 256) -> List[Color]:
    """Reduce a list of colors to n representative ones (simple bucket)."""
    # Not a full k-means; keeps order and dedups. Sufficient for skin usage.
    seen = []
    for c in colors:
        if c not in seen:
            seen.append(c)
        if len(seen) >= n:
            break
    return seen
