"""Realistic shading for skin parts.

Principles extracted from real skin templates: vertical light gradient,
cylindrical edge-darkening (3D illusion), and fabric noise. All functions
operate on a Skin in place and return it for chaining.

``combined`` and ``artistic`` are the same shading engine — cylindrical
edge-darkening times a vertical gradient, with ``artistic`` adding an
optional collar highlight and fabric folds. One internal engine
(``_artistic_engine``) drives both so the two algorithms cannot drift.
"""

from __future__ import annotations

import random

from . import colors
from ._raster import cols, pixels, rows, transform
from .model import Color, FACES
from .skin import Skin


def vertical_gradient(skin: Skin, part, c1: Color, c2: Color,
                      layer: str = "base") -> Skin:
    """Fill a part's faces with a top->bottom gradient."""
    return rows(skin, part, layer,
                lambda j, w, h, face: colors.mix(c1, c2, j / (h - 1 or 1)))


def cylindrical(skin: Skin, part, base: Color, layer: str = "base",
                edge: float = 0.75, center: float = 1.15) -> Skin:
    """Cylindrical lighting: edges dark, center light (3D tube illusion)."""
    return cols(skin, part, layer,
                lambda i, w, h, face: colors.shade(base, _hf(i, w, edge, center)))


def _hf(i: int, w: int, edge: float, center: float) -> float:
    """Horizontal falloff factor at column i of a w-wide face."""
    mid = (w - 1) / 2
    dist = abs(i - mid) / (mid or 1)
    return center - (center - edge) * dist


def _artistic_engine(skin: Skin, part, base: Color, layer: str = "base",
                     *, edge: float, center: float,
                     v_top: float, v_bottom: float,
                     collar: bool, folds: bool) -> Skin:
    """Shared combined/artistic engine: cylindrical x vertical gradient.

    Per physical pixel (i, j): hf from the horizontal falloff, vf from the
    vertical gradient, factor = hf * vf. ``collar`` adds a bright band near
    the top (factor clamped at 1.1 before shading, mirroring the historic
    artistic style); ``folds`` darkens three mid-height rows by a second
    shaded pass (preserving the original double rounding).
    """
    def color_for(i: int, j: int, w: int, h: int, face: str):
        hf = _hf(i, w, edge, center)
        t = j / (h - 1 or 1)
        vf = v_top + (v_bottom - v_top) * t
        factor = hf * vf
        if collar and t < 0.15:
            factor = min(1.1, factor + 0.25 * (1 - t / 0.15))
        c = colors.shade(base, factor)
        if folds and 0 < i < w - 1 and c[3] > 0:
            # Historic behavior: each fold band darkens by 0.75 in turn. On
            # short faces several bands collapse to the same row, so that row
            # is shaded once per collided band — preserve that multiplicity.
            for t in (0.35, 0.5, 0.65):
                if j == int(t * (h - 1)):
                    c = colors.shade(c, 0.75)
        return c
    return pixels(skin, part, layer, color_for)


def combined(skin: Skin, part, base: Color, layer: str = "base",
             edge: float = 0.75, center: float = 1.15,
             v_top: float = 0.9, v_bottom: float = 1.1) -> Skin:
    """Combined gradient + cylindrical shading (most realistic)."""
    return _artistic_engine(skin, part, base, layer, edge=edge, center=center,
                            v_top=v_top, v_bottom=v_bottom,
                            collar=False, folds=False)


def fabric_noise(skin: Skin, part, layer: str = "base",
                 variance: int = 6, seed: int = 0) -> Skin:
    """Add subtle per-pixel noise (cloth texture)."""
    rng = random.Random(seed)
    return transform(
        skin, part, layer,
        lambda i, j, px, w, h, face: colors.add_rgb(px, rng.randint(-variance, variance)))


def outline(skin: Skin, part, color: Color, layer: str = "base",
            width: int = 1) -> Skin:
    """Draw a border around each face of a part."""
    def color_for(i: int, j: int, w: int, h: int, face: str):
        if i < width or i >= w - width or j < width or j >= h - width:
            return color
        return None
    return pixels(skin, part, layer, color_for)


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
                  noise_var: int = 6, seed: int = 0, **kwargs) -> Skin:
    """Apply a shading style to a part. Returns the skin for chaining."""
    if style not in _SHADING_STYLES:
        raise ValueError(f"style must be one of {sorted(_SHADING_STYLES)}")
    _SHADING_STYLES[style](skin, part, base, layer, **kwargs)
    if noise:
        fabric_noise(skin, part, layer, variance=noise_var, seed=seed)
    return skin


# ---------------------------------------------------------------------------
# Style profiles ("风格基因"): map a visual style to artistic/shading params
# ---------------------------------------------------------------------------
# Each profile binds a shading style to the exact artistic.py parameters that
# produce that look — metal highlight, mottled texture, or minimal no-detail.
STYLE_PROFILES = {
    # 极简：纯色，无褶皱无噪点
    "minimal": {"style": "flat"},
    # 干净：轻微圆柱立体，无噪点
    "clean": {"style": "combined", "edge": 0.85, "center": 1.05},
    # 金属高光：强边缘压暗 + 顶部提亮，无褶皱
    "metal": {"style": "artistic", "folds": False, "top_bright": 1.15,
              "bottom_dark": 0.5, "edge_dark": 0.6, "collar": True},
    # 斑驳纹理：褶皱 + 重噪点（布料/旧化）
    "mottled": {"style": "artistic", "folds": True, "noise": True, "noise_var": 8},
    # 皮革：褶皱 + 轻噪点
    "leathery": {"style": "artistic", "folds": True, "noise": True, "noise_var": 5},
}


def apply_style(skin: Skin, part, base: Color, profile: str,
                layer: str = "base", seed: int = 0) -> Skin:
    """Apply a named style profile to a part. Returns the skin for chaining."""
    if profile not in STYLE_PROFILES:
        raise ValueError(f"unknown style profile {profile!r}; "
                         f"choices: {sorted(STYLE_PROFILES)}")
    p = dict(STYLE_PROFILES[profile])
    style = p.pop("style")
    apply_shading(skin, part, base, layer, style=style, seed=seed, **p)
    return skin


def apply_fade(skin: Skin, part, v0: int, v1: int, colors,
               faces=None, layer: str = "base") -> Skin:
    """在 [v0, v1) 行画不透明色阶渐变（消散/渐深，见 techniques §12）。

    逐行应用 colors 色阶（第 v 行用 colors[v-v0]，越界取最后一个），模拟
    「实体 → 幽灵/阴影」的淡出。玩家皮肤做不了半透明，用色阶台阶模拟。

    用法：双腿小腿消散
        apply_fade(s, "right_leg", 9, 12, [GHOST_3, GHOST_2, GHOST_1])
    """
    faces = faces or ("front", "back", "left", "right")
    for v in range(v0, v1):
        color = colors[min(v - v0, len(colors) - 1)]
        for face in faces:
            b = skin.box(part, layer, face)
            lw = b.w // skin.scale
            for u in range(lw):
                skin.pixel(part, layer, face, u, v, color)
    return skin
