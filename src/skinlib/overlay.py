"""Mask-based overlay: composite patterns onto a part without touching its base.

This implements the "多纹理叠加与遮罩" idea from the roadmap: instead of
hard-coding pixel positions, an effect is a *pattern* (per-pixel color) applied
through a *mask* (per-pixel predicate) using a *blend mode*. Battle-damage
scratches, crack lines, and glowing runes are provided as seeded presets.

All effects are deterministic for a given seed, so they're reproducible and
testable.
"""

from __future__ import annotations

import random
from typing import Callable, Optional

from . import colors
from .model import Skin, Color, FACES

# A mask decides, for each logical (face, u, v) of a part, whether an overlay
# applies there. ``None`` means "everywhere".
Mask = Optional[Callable[[str, int, int], bool]]

BLEND_MODES = ("blend", "multiply", "add", "replace")


def _apply_mode(base: Color, ov: Color, mode: str) -> Color:
    """Composite ``ov`` over ``base`` using the given blend mode."""
    if mode == "replace":
        return ov
    if mode == "blend":
        return colors.blend(ov, base)
    if mode == "multiply":
        return tuple(max(0, min(255, round(base[i] * ov[i] / 255)))
                     for i in range(3)) + (base[3],)
    if mode == "add":
        return tuple(max(0, min(255, base[i] + ov[i]))
                     for i in range(3)) + (base[3],)
    raise ValueError(f"mode must be one of {BLEND_MODES}")


# ---------------------------------------------------------------------------
# Mask factories
# ---------------------------------------------------------------------------
def rect_mask(u0: int, v0: int, u1: int, v1: int) -> Callable[[str, int, int], bool]:
    """Mask covering logical rect [u0, u1) x [v0, v1) on every face."""

    def mask(face, u, v):
        return u0 <= u < u1 and v0 <= v < v1

    return mask


def random_mask(density: float, seed: int = 0) -> Callable[[str, int, int], bool]:
    """Mask that is active with probability ``density`` (seeded)."""
    rng = random.Random(seed)

    def mask(face, u, v):
        return rng.random() < density

    return mask


# ---------------------------------------------------------------------------
# General compositor
# ---------------------------------------------------------------------------
def overlay_pattern(skin: Skin, part, pattern, layer: str = "base",
                    mode: str = "blend", mask: Mask = None) -> Skin:
    """Composite a pattern onto a part's faces, restricted by a mask.

    Args:
        skin: target Skin.
        part: body part.
        pattern: a constant RGBA color, or ``callable(face, u, v) -> Color``
            (return ``None`` to skip a pixel).
        layer: base or overlay.
        mode: blend (alpha), multiply (darken), add (brighten/glow), replace.
        mask: optional ``callable(face, u, v) -> bool``.
    """
    if mode not in BLEND_MODES:
        raise ValueError(f"mode must be one of {BLEND_MODES}")
    pat = pattern if callable(pattern) else (lambda face, u, v: pattern)

    for face in FACES:
        lw = skin.box(part, layer, face).w // skin.scale
        lh = skin.box(part, layer, face).h // skin.scale
        for u in range(lw):
            for v in range(lh):
                if mask is not None and not mask(face, u, v):
                    continue
                ov = pat(face, u, v)
                if ov is None:
                    continue
                base = skin.get_pixel(part, layer, face, u, v)
                skin.pixel(part, layer, face, u, v, _apply_mode(base, ov, mode))
    return skin


# ---------------------------------------------------------------------------
# Preset effects (battle damage / runes)
# ---------------------------------------------------------------------------
def scratches(skin: Skin, part, color: Optional[Color] = None,
              layer: str = "base", count: int = 3, length: int = 3,
              seed: int = 0) -> Skin:
    """Battle-damage scratches: short darker diagonal strokes.

    ``color`` defaults to darkening the underlying pixel (a scratch, not a
    repaint), so the base texture shows through.
    """
    rng = random.Random(seed)
    for face in FACES:
        lw = skin.box(part, layer, face).w // skin.scale
        lh = skin.box(part, layer, face).h // skin.scale
        for _ in range(count):
            u = rng.randrange(lw)
            v = rng.randrange(lh)
            for k in range(length):
                uu, vv = u + k, v + k
                if not (0 <= uu < lw and 0 <= vv < lh):
                    continue
                px = skin.get_pixel(part, layer, face, uu, vv)
                if px[3] == 0:
                    continue
                c = color if color is not None else colors.shade(px, 0.45)
                skin.pixel(part, layer, face, uu, vv, c)
    return skin


def cracks(skin: Skin, part, color: Optional[Color] = None,
           layer: str = "base", count: int = 2, seed: int = 0) -> Skin:
    """Crack lines: short branching random walks (stone/metal damage)."""
    rng = random.Random(seed)
    for face in FACES:
        lw = skin.box(part, layer, face).w // skin.scale
        lh = skin.box(part, layer, face).h // skin.scale
        for _ in range(count):
            uu, vv = rng.randrange(lw), rng.randrange(lh)
            for _ in range(max(3, min(lw, lh))):
                if not (0 <= uu < lw and 0 <= vv < lh):
                    break
                px = skin.get_pixel(part, layer, face, uu, vv)
                if px[3] == 0:
                    break
                c = color if color is not None else colors.shade(px, 0.55)
                skin.pixel(part, layer, face, uu, vv, c)
                uu += rng.choice((-1, 0, 1))
                vv += rng.choice((-1, 0, 1))
    return skin


def runes(skin: Skin, part, color: Color = (120, 220, 255, 255),
          layer: str = "base", count: int = 3, seed: int = 0) -> Skin:
    """Glowing glyph marks (cross-shaped strokes) at seeded positions."""
    rng = random.Random(seed)
    glyph = ((0, -1), (0, 0), (0, 1), (1, 0), (-1, 0))
    for face in FACES:
        lw = skin.box(part, layer, face).w // skin.scale
        lh = skin.box(part, layer, face).h // skin.scale
        for _ in range(count):
            u = rng.randrange(1, max(2, lw - 1))
            v = rng.randrange(1, max(2, lh - 1))
            for du, dv in glyph:
                uu, vv = u + du, v + dv
                if (0 <= uu < lw and 0 <= vv < lh
                        and skin.get_pixel(part, layer, face, uu, vv)[3] > 0):
                    skin.pixel(part, layer, face, uu, vv, color)
    return skin


OVERLAYS = {
    "scratches": scratches,
    "cracks": cracks,
    "runes": runes,
}


def apply_overlay(skin: Skin, part, name: str, layer: str = "base",
                  seed: int = 0, **kwargs) -> Skin:
    """Apply a named overlay effect to a part. Returns the skin for chaining."""
    if name not in OVERLAYS:
        raise ValueError(f"unknown overlay {name!r}; choices: {sorted(OVERLAYS)}")
    return OVERLAYS[name](skin, part, layer=layer, seed=seed, **kwargs)
