"""Match a texture's colors to a reference image.

A skin and the cape it is worn with are separate textures, often by different
hands, and they clash: a different hue family, a different temperature, one
noticeably bluer or yellower than the other. An official cape cannot be edited
-- you cannot change what Mojang serves -- so the skin is the part that moves.
The mismatch shows worst on the **back**, where the cape hangs directly against
the body, arms and legs.

The match is done in CIELAB, so it is perceptual rather than per-channel, and
it is measured, so "unified" is a number instead of a hope::

    from skinlib import harmonize, color_difference, region_mask

    color_difference("skin.png", "cape.png")            # 8.6 -- the clash
    harmonize("skin.png", "cape.png").save("matched.png")
    color_difference("matched.png", "cape.png")         # 0.0 -- unified

    back = region_mask(faces=("back",))                 # only where it shows
    color_difference("skin.png", "cape.png", mask=back)  # 8.2 -> the back
    harmonize("skin.png", "cape.png", mask=back).save("back_matched.png")

Two modes, because a shaded skin and a flat logo want different things:

``retheme`` (default)
    Each color adopts the chroma of the reference color nearest to it *in hue*,
    keeping its own lightness -- every shading step survives, the color family
    changes.

``palette``
    Each color moves onto the nearest reference color outright, lightness
    included. Maximum unification; tonal steps collapse when the target has
    more of them than the reference has colors.

``strength`` runs 0 (unchanged) to 1 (fully matched) in both. Pure Pillow +
stdlib, like the rest of skinlib (no numpy).
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Sequence, Tuple, Union

from PIL import Image

from .model import Color, FACES, LAYERS, PARTS, make_layout
from .sampling import palette_of_image

Lab = Tuple[float, float, float]
ImageLike = Union[str, Image.Image]

#: Matching modes, see :func:`harmonize`. ``retheme`` keeps the target's
#: lightness ramp and moves only its color; ``palette`` adopts the reference
#: palette outright.
MODES: Tuple[str, ...] = ("retheme", "palette")


# ---------------------------------------------------------------------------
# sRGB <-> CIELAB (D65)
# ---------------------------------------------------------------------------
def _srgb_to_linear(v: float) -> float:
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055) * 255.0


def rgb_to_lab(color: Sequence[int]) -> Lab:
    """Convert an RGB(A) color to CIELAB under a D65 white point (alpha ignored)."""
    r, g, b = (_srgb_to_linear(float(v)) for v in color[:3])
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    x, y, z = x / 0.95047, y, z / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def lab_to_rgb(lab: Lab, alpha: int = 255) -> Color:
    """Convert a CIELAB color back to sRGB, clamped to the gamut."""
    lightness, a, b = lab
    fy = (lightness + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def finv(t: float) -> float:
        t3 = t ** 3
        return t3 if t3 > 216 / 24389 else (t - 4 / 29) * 108 / 841

    x, y, z = finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b2 = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    return (round(_linear_to_srgb(r)), round(_linear_to_srgb(g)),
            round(_linear_to_srgb(b2)), alpha)


def delta_e(lab_a: Lab, lab_b: Lab) -> float:
    """CIE76 color difference. Under ~2 is imperceptible; over ~5 is obvious."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(lab_a, lab_b)))


# ---------------------------------------------------------------------------
# Reading a texture
# ---------------------------------------------------------------------------
def _as_image(src: ImageLike) -> Image.Image:
    """Accept a path or a PIL image; always hand back RGBA."""
    img = src if isinstance(src, Image.Image) else Image.open(src)
    return img.convert("RGBA")


def _as_mask(mask: Optional[ImageLike],
             size: Tuple[int, int]) -> Optional[Image.Image]:
    if mask is None:
        return None
    m = mask if isinstance(mask, Image.Image) else Image.open(mask)
    m = m.convert("L")
    if m.size != size:
        raise ValueError(f"mask {m.size} does not match image {size}")
    return m


def color_difference(target: ImageLike, reference: ImageLike,
                     palette_size: int = 24,
                     mask: Optional[ImageLike] = None) -> float:
    """Mean ΔE from the target's palette to the reference's nearest colors.

    The headline "color difference" number: how far, on average, each of the
    target's colors sits from the closest color the reference actually uses.
    ``mask`` restricts the target's palette -- pass a
    :func:`region_mask` to measure one region, e.g. the back.
    """
    target_img = _as_image(target)
    ref_img = _as_image(reference)
    ref_pal = palette_of_image(ref_img, max(palette_size, 8), quantize=False)
    if not ref_pal:
        raise ValueError("reference has no opaque pixels")
    target_pal = palette_of_image(target_img, palette_size,
                                  _as_mask(mask, target_img.size),
                                  quantize=False)
    if not target_pal:
        raise ValueError("target has no opaque pixels in the sampled region")
    ref_labs = [rgb_to_lab(c) for c in ref_pal]
    return sum(min(delta_e(rgb_to_lab(t), r) for r in ref_labs)
               for t in target_pal) / len(target_pal)


# ---------------------------------------------------------------------------
# Masking regions
# ---------------------------------------------------------------------------
def region_mask(model: str = "steve", size: int = 64,
                parts: Optional[Sequence[str]] = None,
                layers: Optional[Sequence[str]] = None,
                faces: Optional[Sequence[str]] = None) -> Image.Image:
    """An "L" mask (255 inside) over a selection of skin regions.

    ``parts`` / ``layers`` / ``faces`` each default to everything. The mask is
    how you keep a fix where it shows: ``faces=("back",)`` touches only the
    faces the cape hangs over, ``layers=("overlay",)`` only the clothing,
    ``parts=("body", "left_leg", "right_leg")`` only what sits under it.
    """
    if size not in (64, 128):
        raise ValueError("size must be 64 or 128")
    for name, given, allowed in (("part", parts, PARTS), ("layer", layers, LAYERS),
                                 ("face", faces, FACES)):
        for value in given or ():
            if value not in allowed:
                raise ValueError(f"unknown {name} {value!r}; choices: {sorted(allowed)}")

    scale = size // 64
    layout = make_layout(model)
    mask = Image.new("L", (size, size), 0)
    px = mask.load()
    for part in (parts or PARTS):
        for layer in (layers or LAYERS):
            for face in (faces or FACES):
                box = layout[part][layer].get(face)
                if box is None:                 # slim arms have no 4px band
                    continue
                x0, y0, x1, y1 = box.xyxy
                for y in range(y0 * scale, y1 * scale):
                    for x in range(x0 * scale, x1 * scale):
                        px[x, y] = 255
    return mask


# ---------------------------------------------------------------------------
# The actual matching
# ---------------------------------------------------------------------------
def harmonize(target: ImageLike, reference: ImageLike, mode: str = "retheme",
              strength: float = 1.0, mask: Optional[ImageLike] = None,
              palette_size: int = 24) -> Image.Image:
    """Return ``target`` recolored into ``reference``'s color family.

    ``mode`` decides what is allowed to move:

    ``retheme`` (default)
        Each color adopts the chroma of the reference color closest to it *in
        hue*, keeping its own lightness. A shaded skin keeps every shading step
        -- shadows stay as dark as their author made them -- while the whole
        thing shifts into the reference's color family. This is what you want
        when the target was painted with a deliberate tonal ramp.

    ``palette``
        Each color moves onto the nearest reference color outright, lightness
        included. Maximum unification; a target with more tonal steps than the
        reference has colors will collapse some of them.

    ``strength`` runs 0 (unchanged) to 1 (fully matched) in either mode.
    ``mask`` limits which pixels are touched. Alpha is preserved pixel for
    pixel, fully transparent pixels are left alone, and the two images need not
    match in size -- the reference is only read for statistics. Its colors are
    read exactly, never binned, so a pixel-art cape contributes its real colors.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; choices: {sorted(MODES)}")
    strength = max(0.0, min(1.0, float(strength)))
    out = _as_image(target)
    ref = _as_image(reference)
    ref_pal = palette_of_image(ref, max(palette_size, 8), quantize=False)
    if not ref_pal:
        raise ValueError("reference has no opaque pixels")
    # The reference color to borrow from is always the nearest one in full
    # Lab; the modes differ in what they then take from it. Choosing by hue
    # alone would pair a dark shade with a bright accent's chroma and blow the
    # saturation out.
    ref_labs = [rgb_to_lab(c) for c in ref_pal]

    def nearest(lab: Lab) -> Lab:
        return min(ref_labs, key=lambda r: delta_e(lab, r))

    px = out.load()
    mk = _as_mask(mask, out.size)
    mpx = mk.load() if mk is not None else None
    cache: Dict[Optional[Tuple[int, int, int]], Color] = {}
    for y in range(out.height):
        for x in range(out.width):
            if mpx is not None and mpx[x, y] <= 127:
                continue
            r, g, b, a = px[x, y]
            if a == 0:                          # nothing to recolor
                continue
            key = (r, g, b)
            mapped = cache.get(key)
            if mapped is None:
                lab = rgb_to_lab(key)
                near = nearest(lab)
                if mode == "retheme":
                    blended = (lab[0],
                               lab[1] + (near[1] - lab[1]) * strength,
                               lab[2] + (near[2] - lab[2]) * strength)
                else:
                    blended = tuple(o + (n - o) * strength
                                    for o, n in zip(lab, near))
                mapped = lab_to_rgb(blended)
                cache[key] = mapped
            px[x, y] = (*mapped[:3], a)
    return out


def harmonize_report(target: ImageLike, reference: ImageLike,
                     mode: str = "retheme", strength: float = 1.0,
                     mask: Optional[ImageLike] = None,
                     palette_size: int = 24) -> Dict[str, Any]:
    """Match, measure and describe: ΔE before and after, plus both palettes.

    ``delta_after`` is measured with the same :func:`color_difference`, so it
    is directly comparable to ``delta_before`` -- and both are measured inside
    ``mask`` when one is given.
    """
    before = color_difference(target, reference, palette_size, mask)
    matched = harmonize(target, reference, mode=mode, strength=strength,
                        mask=mask, palette_size=palette_size)
    after = color_difference(matched, reference, palette_size, mask)
    return {
        "mode": mode,
        "strength": strength,
        "delta_before": before,
        "delta_after": after,
        "target_palette": palette_of_image(
            _as_image(target), palette_size,
            _as_mask(mask, _as_image(target).size), quantize=False),
        "reference_palette": palette_of_image(_as_image(reference),
                                              max(palette_size, 8),
                                              quantize=False),
        "image": matched,
    }


__all__ = [
    "MODES", "Lab", "rgb_to_lab", "lab_to_rgb", "delta_e",
    "color_difference", "region_mask", "harmonize", "harmonize_report",
]
