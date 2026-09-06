"""Color utilities for Minecraft skins (pure functions, no state)."""

from __future__ import annotations

from typing import List, Tuple

Color = Tuple[int, int, int, int]


def _clamp(v: float) -> int:
    return max(0, min(255, round(v)))


def parse_color(s: str) -> Color:
    """Parse 'R,G,B', 'R,G,B,A', '#RRGGBB', or '#RRGGBBAA' into RGBA."""
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        if len(h) == 8:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
        raise ValueError(f"bad hex color {s!r}")
    parts = [p.strip() for p in s.split(",")]
    if len(parts) == 3:
        parts.append("255")
    if len(parts) != 4:
        raise ValueError(f"color must be R,G,B[,A] or hex: {s!r}")
    return tuple(int(p) for p in parts)


def mix(c1: Color, c2: Color, t: float) -> Color:
    """Linear interpolation between two RGBA colors (t in [0,1])."""
    t = max(0.0, min(1.0, t))
    return tuple(_clamp(a + (b - a) * t) for a, b in zip(c1, c2))


def shade(color: Color, factor: float) -> Color:
    """Scale RGB by factor (darken <1, lighten >1); alpha unchanged."""
    r, g, b, a = color
    return (_clamp(r * factor), _clamp(g * factor), _clamp(b * factor), a)


def add_rgb(color: Color, d: int) -> Color:
    """Add ``d`` to each RGB channel (clamped); alpha unchanged."""
    r, g, b, a = color
    return (_clamp(r + d), _clamp(g + d), _clamp(b + d), a)


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
