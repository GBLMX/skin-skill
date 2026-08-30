"""Minecraft skin library — a clean, professional toolkit for creating and
editing Minecraft player skins with realistic shading.

Public API (exported intentionally):
    from skinlib import Skin, Color, load, create, shade, sample_palette, render_3d
"""

from __future__ import annotations

from .model import (
    Skin,
    Color,
    Part,
    Layer,
    Face,
    PARTS,
    LAYERS,
    FACES,
    SteveLayout,
    make_layout,
    legacy_to_modern,
    create,
    load,
    parse_color,
)
from .colors import (
    mix,
    shade,
    gray,
    blend,
    gradient,
)
from .shading import (
    apply_shading,
    cylindrical,
    vertical_gradient,
    combined,
    fabric_noise,
    outline,
)
from .artistic import artistic, artistic_full
from .decoration import (
    hat, jacket_front, pants_outline,
    add_highlights, add_shadows, apply_3d_decoration,
)
from .features import face, hair, band
from .patterns import (
    apply_pattern,
    PATTERNS,
    stripes,
    checker,
    camouflage,
)
from .sampling import sample_palette, dominant_colors
from .render import render_3d, render_flat, render_isometric
from .palette import SKIN_TONES, HAIR_COLORS, CLOTHING, ENERGY, all_palettes
from .poses import POSES, get_pose, PartPose
from .validate import validate, validate_report

__all__ = [
    "Skin", "Color", "Part", "Layer", "Face",
    "PARTS", "LAYERS", "FACES",
    "SteveLayout", "make_layout", "legacy_to_modern", "create", "load", "parse_color",
    "mix", "shade", "gray", "blend", "gradient",
    "apply_shading", "cylindrical", "vertical_gradient", "combined",
    "fabric_noise", "outline",
    "artistic", "artistic_full",
    "hat", "jacket_front", "pants_outline",
    "add_highlights", "add_shadows", "apply_3d_decoration",
    "face", "hair", "band",
    "apply_pattern", "PATTERNS", "stripes", "checker", "camouflage",
    "sample_palette", "dominant_colors",
    "render_3d", "render_flat", "render_isometric",
    "SKIN_TONES", "HAIR_COLORS", "CLOTHING", "ENERGY", "all_palettes",
    "POSES", "get_pose", "PartPose",
    "validate", "validate_report",
]

__version__ = "2.2.0"
