"""Reference-image color sampling.

Extract a palette from a character/art reference image so you can build a skin
with matching colors. Uses only the standard library + Pillow (no numpy).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from .model import Color


def _flatten(img: Image.Image) -> List[Tuple[int, int, int]]:
    """Return a list of opaque RGB pixels (ignoring near-transparent)."""
    rgb = img.convert("RGBA")
    out = []
    for r, g, b, a in rgb.getdata():
        if a > 128:
            out.append((r, g, b))
    return out


def dominant_colors(path: str, n: int = 8,
                    resize: int = 64) -> List[Color]:
    """Return the n most common colors as RGBA tuples.

    The image is downscaled first for speed; counts are weighted by frequency.
    """
    img = Image.open(path).convert("RGBA")
    if resize:
        img = img.resize((resize, resize), Image.LANCZOS)
    pixels = _flatten(img)
    if not pixels:
        return [(0, 0, 0, 255)] * n

    counter = Counter(pixels)
    # Merge very-similar colors (quantize to 16 levels per channel)
    quant = Counter()
    for (r, g, b), count in counter.items():
        q = (r // 16 * 16, g // 16 * 16, b // 16 * 16)
        quant[q] += count

    top = [c for c, _ in quant.most_common(n)]
    while len(top) < n:
        top.append(top[-1] if top else (0, 0, 0))
    return [(*rgb, 255) for rgb in top]


def sample_palette(path: str, n: int = 8) -> List[Color]:
    """Alias for dominant_colors; returns a palette of n RGBA colors."""
    return dominant_colors(path, n)


def average_color(path: str) -> Color:
    """Return the average opaque color of an image."""
    img = Image.open(path).convert("RGBA")
    pixels = [px[:3] for px in img.getdata() if px[3] > 128]
    if not pixels:
        return (0, 0, 0, 255)
    n = len(pixels)
    r = sum(p[0] for p in pixels) // n
    g = sum(p[1] for p in pixels) // n
    b = sum(p[2] for p in pixels) // n
    return (r, g, b, 255)
