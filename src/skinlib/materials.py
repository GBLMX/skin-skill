"""Material system: named materials that combine shading, grain texture, and
specular/glow recipes into a single ``apply_material`` call.

A material is a declarative recipe, so users don't need to know which shading
style, noise parameters, or highlight tricks look "right" for leather vs metal:

    apply_material(skin, "body", "leather")
    apply_material(skin, "head", "glow_crystal", color=(120, 60, 160, 255))

Each material is deterministic for a given seed (reproducible pixel output).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from . import colors
from ._noise import Noise2D
from .model import Skin, Color, FACES
from .shading import apply_shading, fabric_noise


def _rgb(r: int, g: int, b: int, a: int = 255) -> Color:
    return (r, g, b, a)


@dataclass(frozen=True)
class Material:
    """A named material recipe.

    Attributes:
        base: default base color (overridable via ``apply_material(color=...)``).
        style: shading style (flat/vertical/cylindrical/combined/artistic).
        shading: extra kwargs forwarded to the shading style.
        grain: texture type — ``None``, ``"fabric"`` (per-pixel noise) or
            ``"perlin"`` (gradient noise for natural grain).
        grain_var: brightness variance applied by the grain pass.
        grain_scale: Perlin frequency (higher = finer grain).
        specular: 0..1 specular streak strength (metallic sheen).
        glow: 0..1 emissive center glow (crystal/energy).
        seed: default random seed (overridable per call).
    """

    name: str
    base: Color
    style: str = "combined"
    shading: Dict = field(default_factory=dict)
    grain: Optional[str] = None
    grain_var: int = 6
    grain_scale: float = 4.0
    specular: float = 0.0
    glow: float = 0.0
    seed: int = 0


MATERIALS: Dict[str, Material] = {
    "cloth": Material(
        name="cloth", base=_rgb(140, 140, 150),
        style="combined", grain="fabric", grain_var=6,
    ),
    "leather": Material(
        name="leather", base=_rgb(120, 85, 55),
        style="artistic", grain="perlin", grain_var=5, grain_scale=6.0,
        specular=0.15,
    ),
    "metal": Material(
        name="metal", base=_rgb(90, 90, 100),
        style="cylindrical", shading={"edge": 0.55, "center": 1.25},
        grain="perlin", grain_var=4, grain_scale=10.0, specular=0.5,
    ),
    "bone": Material(
        name="bone", base=_rgb(220, 215, 200),
        style="combined", grain="perlin", grain_var=3, grain_scale=8.0,
    ),
    "glow_crystal": Material(
        name="glow_crystal", base=_rgb(120, 60, 160),
        style="flat", glow=0.6,
    ),
}


# ---------------------------------------------------------------------------
# Texture / highlight passes
# ---------------------------------------------------------------------------
def _clamp_add(px: Color, d: int) -> Color:
    return (
        max(0, min(255, px[0] + d)),
        max(0, min(255, px[1] + d)),
        max(0, min(255, px[2] + d)),
        px[3],
    )


def noise_grain(skin: Skin, part, layer: str = "base",
                scale: float = 4.0, variance: int = 6, seed: int = 0) -> Skin:
    """Add deterministic Perlin/Simplex grain to a part (natural texture)."""
    noise = Noise2D(seed)
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                px = skin.img.getpixel((x + i, y + j))
                if px[3] == 0:
                    continue
                n = noise.noise2(i / scale, j / scale)  # [-1, 1]
                d = int(round(n * variance))
                skin.img.putpixel((x + i, y + j), _clamp_add(px, d))
    return skin


def specular_streak(skin: Skin, part, base: Color, layer: str = "base",
                    strength: float = 0.5) -> Skin:
    """Add a vertical metallic highlight streak down each face's center."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        mid = w // 2
        for j in range(h):
            if skin.img.getpixel((x + mid, y + j))[3] == 0:
                continue
            skin.img.putpixel((x + mid, y + j), colors.shade(base, 1.0 + strength))
        for off in (mid - 1, mid + 1):
            if 0 <= off < w:
                for j in range(h):
                    if skin.img.getpixel((x + off, y + j))[3] == 0:
                        continue
                    skin.img.putpixel((x + off, y + j),
                                      colors.shade(base, 1.0 + strength * 0.5))
    return skin


def glow_center(skin: Skin, part, base: Color, layer: str = "base",
                strength: float = 0.6) -> Skin:
    """Add an emissive center that fades toward the edges (crystal/energy)."""
    for face in FACES:
        x, y, w, h = skin.region(part, layer, face)
        midx = (w - 1) / 2
        midy = (h - 1) / 2
        for i in range(w):
            for j in range(h):
                px = skin.img.getpixel((x + i, y + j))
                if px[3] == 0:
                    continue
                dx = abs(i - midx) / (midx or 1)
                dy = abs(j - midy) / (midy or 1)
                dist = max(dx, dy)
                skin.img.putpixel((x + i, y + j),
                                  colors.shade(base, 1.0 + strength * (1.0 - dist)))
    return skin


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def apply_material(skin: Skin, part, name, color: Optional[Color] = None,
                   layer: str = "base", seed: Optional[int] = None) -> Skin:
    """Apply a named material to a part. Returns the skin for chaining.

    Args:
        skin: target Skin.
        part: body part (head/body/right_arm/...).
        name: material name in ``MATERIALS`` or a ``Material`` instance.
        color: override the material's default base color.
        layer: base or overlay.
        seed: override the material's default random seed.
    """
    if isinstance(name, str):
        if name not in MATERIALS:
            raise ValueError(f"unknown material {name!r}; choices: {sorted(MATERIALS)}")
        mat = MATERIALS[name]
    else:
        mat = name

    base = color or mat.base
    s = seed if seed is not None else mat.seed

    apply_shading(skin, part, base, layer, style=mat.style, **mat.shading)

    if mat.grain == "fabric":
        fabric_noise(skin, part, layer, variance=mat.grain_var, seed=s)
    elif mat.grain == "perlin":
        noise_grain(skin, part, layer, scale=mat.grain_scale,
                    variance=mat.grain_var, seed=s)

    if mat.specular:
        specular_streak(skin, part, base, layer, strength=mat.specular)
    if mat.glow:
        glow_center(skin, part, base, layer, strength=mat.glow)

    return skin
