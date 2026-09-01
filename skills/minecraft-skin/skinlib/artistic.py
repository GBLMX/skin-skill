"""Artistic shading based on real Minecraft skin analysis.

This encodes the specific lighting/preesentation patterns observed in
professional skins (双色卫衣, Blockbench player_skin):

1. Vertical gradient: strong top-highlight -> bottom-shadow (brightness span ~220)
2. Horizontal symmetric falloff: center bright, edges slightly dark (~40)
3. Collar/cuff highlight: a bright band near the top edge
4. Fabric folds: subtle darker bands mid-body
5. Heavy bottom shadow: near-black at the very bottom

The `artistic` style produces skins that look hand-drawn rather than flat-filled.
"""

from __future__ import annotations

from . import colors
from .model import Skin, Color, FACES


def artistic(skin: Skin, part, base: Color, layer: str = "base",
             top_bright: float = 1.0, bottom_dark: float = 0.35,
             edge_dark: float = 0.85, collar: bool = True,
             folds: bool = True) -> Skin:
    """Apply observed realistic lighting to a part.

    Parameters:
        top_bright: brightness multiplier at the top (1.0 = base color)
        bottom_dark: brightness multiplier at the bottom (0.35 = dark)
        edge_dark: brightness multiplier at left/right edges
        collar: add a bright band near the top (collar/cuff highlight)
        folds: add subtle darker bands mid-height (fabric folds)
    """
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            # horizontal falloff (center bright -> edges dark)
            mid = (w - 1) / 2
            hdist = abs(i - mid) / (mid or 1)
            hf = 1.0 - (1.0 - edge_dark) * hdist

            for j in range(h):
                # vertical gradient top -> bottom
                t = j / (h - 1 or 1)
                vf = top_bright + (bottom_dark - top_bright) * t

                factor = hf * vf

                # collar highlight: bright band near the top (first ~15%)
                if collar and t < 0.15:
                    factor = min(1.1, factor + 0.25 * (1 - t / 0.15))

                c = colors.shade(base, factor)
                skin.img.putpixel((x + i, y + j), c)

        # fabric folds: darker horizontal bands mid-height
        if folds:
            for band_t in (0.35, 0.5, 0.65):
                j = int(band_t * (h - 1))
                for i in range(1, w - 1):
                    px = skin.img.getpixel((x + i, y + j))
                    if px[3] > 0:
                        c = colors.shade(px, 0.75)
                        skin.img.putpixel((x + i, y + j), c)

    return skin
