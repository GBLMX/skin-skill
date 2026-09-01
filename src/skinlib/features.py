"""Character features: facial details, 3D hair, and wrap-around bands.

Reusable helpers for the finishing touches that make a skin look complete:

- ``face()`` — brows / eyes / nose / mouth / chin on the head front
- ``hair()`` — two-layer (base + overlay) hair with 3D volume
- ``band()`` — a horizontal band wrapped around all four vertical faces
"""

from __future__ import annotations

from typing import Optional

from .model import Skin, Color


def _lighter(c: Color, d: int = 30) -> Color:
    return tuple(min(255, x + d) for x in c[:3]) + (c[3],)


def _darker(c: Color, d: int = 48) -> Color:
    return tuple(max(0, x - d) for x in c[:3]) + (c[3],)


def face(skin: Skin,
         eye_color: Color = (96, 226, 140, 255),
         eye_hot: Optional[Color] = None,
         brow_color: Color = (120, 110, 105, 255),
         mouth_color: Color = (110, 92, 88, 255),
         nose_shade: Color = (150, 140, 130, 255)) -> Skin:
    """Draw facial details on the head front (base layer).

    Assumes the head base is already painted with skin color. Adds brows at
    v=3, eyes at v=4 (2px each, with a hot highlight), nose at v=5, mouth at
    v=6, and chin shading at v=7. Returns the skin for chaining.
    """
    if eye_hot is None:
        eye_hot = _lighter(eye_color, 90)

    # brows
    for u in (1, 6):
        skin.pixel("head", "base", "front", u, 3, brow_color)
    # eyes (2px each side) + hot center
    for u in (1, 2, 5, 6):
        skin.pixel("head", "base", "front", u, 4, eye_color)
    skin.pixel("head", "base", "front", 2, 4, eye_hot)
    skin.pixel("head", "base", "front", 5, 4, eye_hot)
    # nose
    for u in (3, 4):
        skin.pixel("head", "base", "front", u, 5, nose_shade)
    # mouth
    for u in (3, 4):
        skin.pixel("head", "base", "front", u, 6, mouth_color)
    # chin shading
    for u in (3, 4):
        skin.pixel("head", "base", "front", u, 7, nose_shade)
    return skin


def hair(skin: Skin, color: Color,
         light: Optional[Color] = None,
         dark: Optional[Color] = None) -> Skin:
    """Add two-layer hair (base + overlay 3D volume) to the head.

    Covers the top, the back (long hair), and the upper half of the sides;
    the front keeps a thin fringe plus side strands so the face stays
    visible. ``light``/``dark`` default to derived strand tones.
    """
    light = light or _lighter(color, 30)
    dark = dark or _darker(color, 48)

    # top / back / side upper-half on both layers
    for layer in ("base", "overlay"):
        skin.paint_face("head", layer, "top", color)
        skin.paint_face("head", layer, "back", color)
        for face in ("left", "right"):
            for u in range(8):
                for v in range(4):
                    skin.pixel("head", layer, face, u, v, color)

    # front fringe + side strands (keeps the face exposed)
    for u in range(8):
        skin.pixel("head", "base", "front", u, 0, color)
        skin.pixel("head", "overlay", "front", u, 0, color)
    for u in (0, 1, 6, 7):
        skin.pixel("head", "base", "front", u, 1, color)
    for u in (0, 7):
        for v in (1, 2, 3):
            skin.pixel("head", "overlay", "front", u, v, color)

    # strand texture (base)
    for u in (1, 4, 6):
        for v in range(8):
            skin.pixel("head", "base", "back", u, v, light)
    for face in ("left", "right"):
        for v in range(4):
            skin.pixel("head", "base", face, 3, v, light)
            skin.pixel("head", "base", face, 6, v, dark)
    for u in (3, 4):
        skin.pixel("head", "base", "top", u, 0, light)

    # strand texture (overlay)
    for u in (2, 5):
        for v in range(4):
            skin.pixel("head", "overlay", "top", u, v, light)
    for u in range(8):
        skin.pixel("head", "overlay", "back", u, 7, dark)
        skin.pixel("head", "overlay", "back", u, 6, light)
    for face in ("left", "right"):
        for v in range(4):
            skin.pixel("head", "overlay", face, 3, v, light)
            skin.pixel("head", "overlay", face, 6, v, dark)
    return skin


def band(skin: Skin, part, v0: int, v1: int, color: Color,
         layer: str = "overlay", dark: Optional[Color] = None) -> Skin:
    """Paint a horizontal band across all four vertical faces of a part.

    Wraps front/back/left/right so belts, straps, wrist and knee guards look
    continuous. ``v0``/``v1`` are inclusive row indices within each face.
    """
    dark = dark or _darker(color, 40)
    for face in ("front", "back", "left", "right"):
        x, y, w, h = skin.region(part, layer, face)
        lw, lh = w // skin.scale, h // skin.scale
        for u in range(lw):
            for v in range(v0, v1 + 1):
                if 0 <= v < lh:
                    skin.pixel(part, layer, face, u, v,
                               dark if v == v1 else color)
    return skin
