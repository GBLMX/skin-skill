"""Artistic shading based on real Minecraft skin analysis.

This encodes the specific lighting/preesentation patterns observed in
professional skins (双色卫衣, Blockbench player_skin):

1. Vertical gradient: strong top-highlight -> bottom-shadow (brightness span ~220)
2. Horizontal symmetric falloff: center bright, edges slightly dark (~40)
3. Collar/cuff highlight: a bright band near the top edge
4. Fabric folds: subtle darker bands mid-body
5. Heavy bottom shadow: near-black at the very bottom

The `artistic` style produces skins that look hand-drawn rather than flat-filled.

``artistic`` shares its engine with ``shading.combined`` (see
``shading._artistic_engine``) — the two differ only in defaults and the extra
collar/folds passes.
"""

from __future__ import annotations

from .model import Color
from .skin import Skin


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
    from .shading import _artistic_engine
    return _artistic_engine(
        skin, part, base, layer,
        edge=edge_dark, center=1.0,
        v_top=top_bright, v_bottom=bottom_dark,
        collar=collar, folds=folds)
