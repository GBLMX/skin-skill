"""Minecraft skin library — a clean, professional toolkit for creating and
editing Minecraft player skins with realistic shading.

Public API (exported intentionally):
    from skinlib import Skin, Color, load, create, shade, sample_palette, render_3d
"""

from __future__ import annotations

from .model import (
    Color,
    Part,
    Layer,
    Face,
    PARTS,
    LAYERS,
    FACES,
    SteveLayout,
    make_layout,
)
from .skin import (
    Skin,
    create,
    load,
)
from .transforms import (
    legacy_to_modern,
    detect_model,
    strip_matte,
)
from .colors import (
    mix,
    shade,
    gray,
    blend,
    gradient,
    parse_color,
)
from .shading import (
    apply_shading,
    apply_style,
    apply_fade,
    STYLE_PROFILES,
    SHADING_STYLES,
    cylindrical,
    vertical_gradient,
    combined,
    fabric_noise,
    outline,
)
from .artistic import artistic
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
from .sampling import sample_palette, dominant_colors, palette_of_image
from .render import render_3d, render_flat, render_isometric
from .palette import SKIN_TONES, HAIR_COLORS, CLOTHING, ENERGY, all_palettes
from .poses import POSES, get_pose, PartPose
from .validate import validate, validate_report
from .templates import build_template, TEMPLATES
from .materials import (
    Material,
    MATERIALS,
    apply_material,
    noise_grain,
    specular_streak,
    glow_center,
)
from .overlay import (
    overlay_pattern,
    apply_overlay,
    OVERLAYS,
    rect_mask,
    random_mask,
    scratches,
    cracks,
    runes,
)
from .recipe import generate_from_recipe, recipe_to_python, OPS
from .harmonize import (
    harmonize,
    harmonize_report,
    color_difference,
    region_mask,
)
from .texture import (
    Texture,
    block,
    icon,
    from_spec,
    generate,
    texture_size,
    TEXTURE_SIZES,
    BLOCK_FACES,
    ICON_ART,
)
from .pack import build_pack, pack_format, pack_meta
# Exposed as a namespace, not flattened: the vanilla data layer needs the
# optional minebase extra and pulls in a large dataset surface.
from . import gamedata

__all__ = [
    "Skin", "Color", "Part", "Layer", "Face",
    "PARTS", "LAYERS", "FACES",
    "SteveLayout", "make_layout", "legacy_to_modern", "detect_model",
    "strip_matte", "create", "load", "parse_color",
    "mix", "shade", "gray", "blend", "gradient",
    "apply_shading", "apply_style", "apply_fade", "STYLE_PROFILES", "SHADING_STYLES", "cylindrical", "vertical_gradient", "combined",
    "fabric_noise", "outline",
    "artistic",
    "hat", "jacket_front", "pants_outline",
    "add_highlights", "add_shadows", "apply_3d_decoration",
    "face", "hair", "band",
    "apply_pattern", "PATTERNS", "stripes", "checker", "camouflage",
    "sample_palette", "dominant_colors", "palette_of_image",
    "render_3d", "render_flat", "render_isometric",
    "SKIN_TONES", "HAIR_COLORS", "CLOTHING", "ENERGY", "all_palettes",
    "build_template", "TEMPLATES",
    "POSES", "get_pose", "PartPose",
    "validate", "validate_report",
    "Material", "MATERIALS", "apply_material",
    "noise_grain", "specular_streak", "glow_center",
    "overlay_pattern", "apply_overlay", "OVERLAYS",
    "rect_mask", "random_mask", "scratches", "cracks", "runes",
    "generate_from_recipe", "recipe_to_python", "OPS",
    "harmonize", "harmonize_report", "color_difference", "region_mask",
    "Texture", "block", "icon", "from_spec", "generate",
    "texture_size", "TEXTURE_SIZES", "BLOCK_FACES", "ICON_ART",
    "build_pack", "pack_format", "pack_meta",
    "gamedata",
]

__version__ = "3.5.0"
