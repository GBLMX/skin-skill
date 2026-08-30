"""Realistic shading for skin parts.

Principles extracted from real skin templates: vertical light gradient,
cylindrical edge-darkening (3D illusion), and fabric noise. All functions
operate on a Skin in place and return it for chaining.
"""

from __future__ import annotations

import random
from typing import Optional

from . import colors
from .model import Skin, Color, FACES, PARTS


def vertical_gradient(skin: Skin, part, c1: Color, c2: Color,
                      layer: str = "base") -> Skin:
    """Fill a part's faces with a top->bottom gradient."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for j in range(h):
            c = colors.mix(c1, c2, j / (h - 1 or 1))
            skin.draw.line((x, y + j, x + w - 1, y + j), fill=c)
    return skin


def cylindrical(skin: Skin, part, base: Color, layer: str = "base",
                edge: float = 0.75, center: float = 1.15) -> Skin:
    """Cylindrical lighting: edges dark, center light (3D tube illusion)."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        mid = (w - 1) / 2
        for i in range(w):
            dist = abs(i - mid) / (mid or 1)
            factor = center - (center - edge) * dist
            c = colors.shade(base, factor)
            skin.draw.line((x + i, y, x + i, y + h - 1), fill=c)
    return skin


def combined(skin: Skin, part, base: Color, layer: str = "base",
             edge: float = 0.75, center: float = 1.15,
             v_top: float = 0.9, v_bottom: float = 1.1) -> Skin:
    """Combined gradient + cylindrical shading (most realistic)."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        mid = (w - 1) / 2
        for i in range(w):
            dist = abs(i - mid) / (mid or 1)
            hf = center - (center - edge) * dist
            for j in range(h):
                t = j / (h - 1 or 1)
                vf = v_top + (v_bottom - v_top) * t
                c = colors.shade(base, hf * vf)
                skin.img.putpixel((x + i, y + j), c)
    return skin


def fabric_noise(skin: Skin, part, layer: str = "base",
                 variance: int = 6, seed: int = 0) -> Skin:
    """Add subtle per-pixel noise (cloth texture)."""
    rng = random.Random(seed)
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                px = skin.img.getpixel((x + i, y + j))
                if px[3] == 0:
                    continue
                d = rng.randint(-variance, variance)
                skin.img.putpixel(
                    (x + i, y + j),
                    (max(0, min(255, px[0] + d)),
                     max(0, min(255, px[1] + d)),
                     max(0, min(255, px[2] + d)),
                     px[3]))
    return skin


def outline(skin: Skin, part, color: Color, layer: str = "base",
            width: int = 1) -> Skin:
    """Draw a border around each face of a part."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                if i < width or i >= w - width or j < width or j >= h - width:
                    skin.img.putpixel((x + i, y + j), color)
    return skin


# ---------------------------------------------------------------------------
# High-level dispatcher
# ---------------------------------------------------------------------------
def _artistic(s, p, b, l, **k):
    from .artistic import artistic
    return artistic(s, p, b, l, **k)


_SHADING_STYLES = {
    "flat": lambda s, p, b, l, **k: s.paint_part(p, b, l),
    "vertical": lambda s, p, b, l, **k: vertical_gradient(
        s, p, colors.shade(b, 1.1), colors.shade(b, 0.85), l),
    "cylindrical": lambda s, p, b, l, **k: cylindrical(s, p, b, l, **k),
    "combined": lambda s, p, b, l, **k: combined(s, p, b, l, **k),
    "artistic": _artistic,
}


def apply_shading(skin: Skin, part, base: Color, layer: str = "base",
                  style: str = "combined", noise: bool = False,
                  noise_var: int = 6, **kwargs) -> Skin:
    """Apply a shading style to a part. Returns the skin for chaining."""
    if style not in _SHADING_STYLES:
        raise ValueError(f"style must be one of {sorted(_SHADING_STYLES)}")
    _SHADING_STYLES[style](skin, part, base, layer, **kwargs)
    if noise:
        fabric_noise(skin, part, layer, variance=noise_var)
    return skin
