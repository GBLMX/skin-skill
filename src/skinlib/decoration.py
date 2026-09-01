"""3D decoration: sparse overlay layers + highlight/shadow accents.

Encodes the 3D-depth techniques observed in real skins (双色卫衣):
- Sparse second layer (not full coverage) so clothing appears to float
- Highlight pixels (bright) at raised points
- Shadow pixels (dark) at recessed edges
- Woven texture (alternating brightness) for fabric

This is what makes a skin look 3D rather than flat.
"""

from __future__ import annotations

from typing import Optional

from . import colors
from .model import Skin, Color, FACES


# ---------------------------------------------------------------------------
# Sparse overlay helpers
# ---------------------------------------------------------------------------
def hat(skin: Skin, color: Color, top_color: Optional[Color] = None,
        weave: bool = True) -> Skin:
    """Add a hat on the head overlay (sparse: top + rim only, face exposed).

    Mimics the 双色卫衣 hat: covers top and side rims, leaves the lower
    front (face) transparent. Optional weave alternates brightness for fabric.
    """
    top = top_color or color
    s = skin.scale
    # top face: full with weave
    x, y, w, h = skin.region("head", "overlay", "top")
    for i in range(w):
        for j in range(h):
            if weave and (i + j) % 2 == 0:
                skin.img.putpixel((x + i, y + j), colors.shade(top, 0.85))
            else:
                skin.img.putpixel((x + i, y + j), top)

    # front/back/left/right: only upper rim (top 3 logical rows)
    for face in ("front", "back", "left", "right"):
        x, y, w, h = skin.region("head", "overlay", face)
        for i in range(w):
            for j in range(0, 3 * s):
                skin.img.putpixel((x + i, y + j), color)
    # front: a couple of highlight pixels (light reflection)
    x, y, w, h = skin.region("head", "overlay", "front")
    skin.img.putpixel((x + 2 * s, y + 1 * s), colors.shade(color, 1.3))
    skin.img.putpixel((x + w - 3 * s, y + 1 * s), colors.shade(color, 1.3))
    return skin


def jacket_front(skin: Skin, color: Color, highlight: Optional[Color] = None) -> Skin:
    """Add a sparse jacket/front-chest design (like a logo or zipper)."""
    hi = highlight or colors.shade(color, 1.3)
    s = skin.scale
    x, y, w, h = skin.region("body", "overlay", "front")
    # vertical zipper line at center, with highlight pixels
    for j in range(3 * s, 9 * s):
        skin.img.putpixel((x + w // 2, y + j), colors.shade(color, 0.7))
        if j in (3 * s, 5 * s, 7 * s):
            skin.img.putpixel((x + w // 2 + 1, y + j), hi)
    return skin


def pants_outline(skin: Skin, color: Color, highlight: Optional[Color] = None) -> Skin:
    """Add sparse pants second layer (bottom hem + highlight)."""
    hi = highlight or colors.shade(color, 1.3)
    for leg in ("right_leg", "left_leg"):
        for face in ("front", "back"):
            x, y, w, h = skin.region(leg, "overlay", face)
            # bottom hem (last 2 rows)
            for i in range(w):
                skin.img.putpixel((x + i, y + h - 2), color)
                skin.img.putpixel((x + i, y + h - 1), colors.shade(color, 0.7))
            # a highlight line just above hem
            for i in range(1, w - 1):
                skin.img.putpixel((x + i, y + h - 3), hi)
    return skin


# ---------------------------------------------------------------------------
# Highlight / shadow accents (3D depth on the base layer)
# ---------------------------------------------------------------------------
def add_highlights(skin: Skin, part, color: Color, layer: str = "base",
                   intensity: float = 1.3, positions=None) -> Skin:
    """Add highlight pixels (bright accents) to suggest raised areas."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        pts = positions or [(w // 2, 1), (w // 2, h // 3)]
        for u, v in pts:
            if 0 <= u < w and 0 <= v < h:
                skin.img.putpixel((x + u, y + v), colors.shade(color, intensity))
    return skin


def add_shadows(skin: Skin, part, color: Color, layer: str = "base",
                intensity: float = 0.6) -> Skin:
    """Add shadow pixels (dark) along bottom/edges for depth."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        # bottom row shadow
        for i in range(w):
            skin.img.putpixel((x + i, y + h - 1), colors.shade(color, intensity))
        # side edges shadow
        for j in range(h):
            skin.img.putpixel((x, y + j), colors.shade(color, intensity * 0.9))
            skin.img.putpixel((x + w - 1, y + j), colors.shade(color, intensity * 0.9))
    return skin


# ---------------------------------------------------------------------------
# One-shot: apply full 3D decoration to a skin
# ---------------------------------------------------------------------------
def apply_3d_decoration(skin: Skin, hat_color=None, jacket_color=None,
                        pants_color=None) -> Skin:
    """Apply the full 3D decoration pipeline (sparse overlay + depth)."""
    if hat_color:
        hat(skin, hat_color)
    if jacket_color:
        jacket_front(skin, jacket_color)
    if pants_color:
        pants_outline(skin, pants_color)
    return skin
