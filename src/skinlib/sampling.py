"""Reference-image color sampling.

Extract a palette from a character/art reference image so you can build a skin
with matching colors. Uses only the standard library + Pillow (no numpy).
"""

from __future__ import annotations

from collections import Counter
from typing import List, Optional

from PIL import Image

from .model import Color


def palette_of_image(img: Image.Image, n: int = 8,
                     mask: Optional[Image.Image] = None,
                     quantize: bool = True) -> List[Color]:
    """The n most common colors of an in-memory image, as RGBA tuples.

    Near-transparent pixels never count. ``mask`` -- an "L" image the same size
    as ``img`` -- restricts which pixels are sampled, e.g. to one layer or body
    part. Near-identical colors are merged (quantize levels per channel) so a
    noisy source still yields distinct entries. Returns fewer than ``n`` when
    the image simply has fewer distinct colors, and ``[]`` when it is empty.

    Pass ``quantize=False`` to keep the exact colors -- what color matching
    wants, since binning to 16 levels darkens every entry by up to 15 and a
    pixel-art reference has distinct colors already.
    """
    rgba = img.convert("RGBA")
    if mask is not None and mask.size != rgba.size:
        raise ValueError(f"mask {mask.size} does not match image {rgba.size}")

    px = rgba.load()
    mk = mask.convert("L").load() if mask is not None else None
    counts: Counter = Counter()
    for y in range(rgba.height):
        for x in range(rgba.width):
            if mk is not None and mk[x, y] <= 127:
                continue
            r, g, b, a = px[x, y]
            if a > 128:
                counts[(r, g, b)] += 1
    if not counts:
        return []
    if not quantize:
        return [(*rgb, 255) for rgb, _ in counts.most_common(n)]

    quant: Counter = Counter()
    for (r, g, b), count in counts.items():
        quant[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += count
    return [(*rgb, 255) for rgb, _ in quant.most_common(n)]


def dominant_colors(path: str, n: int = 8,
                    resize: int = 64) -> List[Color]:
    """Return the n most common colors as RGBA tuples.

    The image is downscaled first for speed; counts are weighted by frequency.
    """
    img = Image.open(path).convert("RGBA")
    if resize:
        img = img.resize((resize, resize), Image.LANCZOS)
    palette = palette_of_image(img, n)
    if not palette:
        return [(0, 0, 0, 255)] * n
    while len(palette) < n:                 # fewer distinct colors than asked
        palette.append(palette[-1])
    return palette


def sample_palette(path: str, n: int = 8) -> List[Color]:
    """Alias for dominant_colors; returns a palette of n RGBA colors."""
    return dominant_colors(path, n)
