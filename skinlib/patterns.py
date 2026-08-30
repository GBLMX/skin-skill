"""Decorative patterns for skin parts (stripes, checker, camouflage, etc.)."""

from __future__ import annotations

import random
from typing import List

from .model import Skin, Color, FACES


def stripes(skin: Skin, part, c1: Color, c2: Color, layer: str = "base",
            direction: str = "vertical", width: int = 2) -> Skin:
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        if direction == "vertical":
            for i in range(w):
                c = c1 if (i // width) % 2 == 0 else c2
                skin.draw.line((x + i, y, x + i, y + h - 1), fill=c)
        else:
            for j in range(h):
                c = c1 if (j // width) % 2 == 0 else c2
                skin.draw.line((x, y + j, x + w - 1, y + j), fill=c)
    return skin


def checker(skin: Skin, part, c1: Color, c2: Color, layer: str = "base",
            cell: int = 4) -> Skin:
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                c = c1 if ((i // cell) + (j // cell)) % 2 == 0 else c2
                skin.img.putpixel((x + i, y + j), c)
    return skin


def camouflage(skin: Skin, palette: List[Color], part: str = "body",
               layer: str = "base", seed: int = 0) -> Skin:
    """Fill a part with random camouflage using a color palette."""
    rng = random.Random(seed)
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                skin.img.putpixel((x + i, y + j), rng.choice(palette))
    return skin


def border_trim(skin: Skin, part, fill: Color, trim: Color, layer: str = "base",
                width: int = 1) -> Skin:
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        skin.draw.rectangle((x, y, x + w, y + h), fill=fill)
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
