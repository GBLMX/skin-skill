"""Decorative patterns for skin parts (stripes, checker, camouflage, etc.)."""

from __future__ import annotations

import random
from typing import List

from ._raster import cols, pixels, rows
from .model import Color, canvas_faces
from .skin import Skin


def stripes(skin: Skin, part, c1: Color, c2: Color, layer: str = "base",
            direction: str = "vertical", width: int = 2) -> Skin:
    if direction == "vertical":
        return cols(skin, part, layer,
                    lambda i, w, h, face: c1 if (i // width) % 2 == 0 else c2)
    return rows(skin, part, layer,
                lambda j, w, h, face: c1 if (j // width) % 2 == 0 else c2)


def checker(skin: Skin, part, c1: Color, c2: Color, layer: str = "base",
            cell: int = 4) -> Skin:
    return pixels(
        skin, part, layer,
        lambda i, j, w, h, face: c1 if ((i // cell) + (j // cell)) % 2 == 0 else c2)


def camouflage(skin: Skin, palette: List[Color], part: str = "body",
               layer: str = "base", seed: int = 0) -> Skin:
    """Fill a part with random camouflage using a color palette."""
    rng = random.Random(seed)
    return pixels(skin, part, layer,
                  lambda i, j, w, h, face: rng.choice(palette))


def border_trim(skin: Skin, part, fill: Color, trim: Color, layer: str = "base",
                width: int = 1) -> Skin:
    for face in canvas_faces(skin):
        x, y, w, h = skin.region(part, layer, face)
        skin.draw.rectangle((x, y, x + w - 1, y + h - 1), fill=fill)
        skin.draw.rectangle((x, y, x + w - 1, y + h - 1), outline=trim, width=width)
    return skin


PATTERNS = {
    "stripes": stripes,
    "checker": checker,
    "camouflage": camouflage,
    "border_trim": border_trim,
}


def apply_pattern(skin: Skin, name: str, *args, **kwargs) -> Skin:
    if name not in PATTERNS:
        raise ValueError(f"unknown pattern {name!r}; choices: {sorted(PATTERNS)}")
    return PATTERNS[name](skin, *args, **kwargs)
