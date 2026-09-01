"""Preset character templates built with the shading API."""

from __future__ import annotations

from .model import Skin
from .shading import apply_shading, apply_style
from .materials import apply_material
from .features import face, band
from .palette import SKIN_TONES, CLOTHING


def knight() -> Skin:
    s = Skin(size=64)
    silver = (200, 200, 210, 255)
    dark = (80, 80, 90, 255)
    skin_tone = (240, 190, 150, 255)
    red = (160, 40, 40, 255)

    apply_shading(s, "head", skin_tone, "base", style="combined")
    apply_shading(s, "head", silver, "overlay", style="combined")
    apply_shading(s, "body", silver, "base", style="combined")
    apply_shading(s, "body", dark, "overlay", style="combined")
    apply_shading(s, "right_arm", silver, "base", style="cylindrical")
    apply_shading(s, "left_arm", silver, "base", style="cylindrical")
    apply_shading(s, "right_leg", dark, "base", style="cylindrical")
    apply_shading(s, "left_leg", dark, "base", style="cylindrical")
    apply_shading(s, "right_leg", red, "overlay", style="cylindrical")
    apply_shading(s, "left_leg", red, "overlay", style="cylindrical")
    return s


def villager() -> Skin:
    s = Skin(size=64)
    skin_tone = (220, 170, 130, 255)
    robe = (120, 80, 40, 255)
    robe_dark = (90, 60, 30, 255)
    hat = (140, 100, 60, 255)

    apply_shading(s, "head", skin_tone, "base", style="combined")
    apply_shading(s, "head", hat, "overlay", style="combined")
    apply_shading(s, "body", robe, "base", style="combined", noise=True)
    apply_shading(s, "body", robe_dark, "overlay", style="combined")
    apply_shading(s, "right_arm", robe, "base", style="cylindrical")
    apply_shading(s, "left_arm", robe, "base", style="cylindrical")
    apply_shading(s, "right_leg", robe_dark, "base", style="cylindrical")
    apply_shading(s, "left_leg", robe_dark, "base", style="cylindrical")
    return s


def astronaut() -> Skin:
    s = Skin(size=64)
    white = (240, 240, 245, 255)
    gray = (190, 190, 200, 255)

    apply_shading(s, "head", gray, "base", style="combined")
    apply_shading(s, "head", white, "overlay", style="combined")
    apply_shading(s, "body", white, "base", style="combined")
    apply_shading(s, "body", gray, "overlay", style="combined")
    for p in ("right_arm", "left_arm", "right_leg", "left_leg"):
        apply_shading(s, p, white, "base", style="cylindrical")
    return s


def noob() -> Skin:
    """The classic 'noob' skin: a fixed black/gray palette, minimal detail."""
    s = Skin(size=64)
    apply_shading(s, "head", SKIN_TONES["steve_classic"], "base", style="combined")
    apply_style(s, "body", CLOTHING["gray"], "minimal")
    apply_style(s, "right_arm", CLOTHING["gray"], "minimal")
    apply_style(s, "left_arm", CLOTHING["gray"], "minimal")
    apply_style(s, "right_leg", CLOTHING["black"], "minimal")
    apply_style(s, "left_leg", CLOTHING["black"], "minimal")
    apply_shading(s, "body", CLOTHING["dark_gray"], "overlay", style="combined")
    return s


def herobrine() -> Skin:
    """Herobrine: Steve's palette with glowing white eyes."""
    s = Skin(size=64)
    shirt = (0, 150, 160, 255)
    pants = (60, 40, 160, 255)
    apply_shading(s, "head", SKIN_TONES["steve_classic"], "base", style="combined")
    apply_style(s, "body", shirt, "clean")
    apply_style(s, "right_arm", shirt, "clean")
    apply_style(s, "left_arm", shirt, "clean")
    apply_style(s, "right_leg", pants, "clean")
    apply_style(s, "left_leg", pants, "clean")
    face(s, eye_color=(255, 255, 255, 255))
    return s


def medieval_knight() -> Skin:
    """Medieval knight: metal plate + red tunic + gold belt."""
    s = Skin(size=64)
    red = (160, 40, 40, 255)
    gold = (210, 170, 60, 255)
    apply_shading(s, "head", SKIN_TONES["tan"], "base", style="combined")
    apply_material(s, "head", "metal", layer="overlay")        # helmet
    apply_material(s, "body", "metal")                          # plate body
    apply_shading(s, "body", red, "overlay", style="artistic")  # tunic
    apply_material(s, "right_arm", "metal")
    apply_material(s, "left_arm", "metal")
    apply_material(s, "right_leg", "metal")
    apply_material(s, "left_leg", "metal")
    band(s, "body", 5, 6, gold, layer="overlay")                # gold belt
    return s


TEMPLATES = {
    "knight": knight,
    "villager": villager,
    "astronaut": astronaut,
    "noob": noob,
    "herobrine": herobrine,
    "medieval_knight": medieval_knight,
}


def build_template(name: str) -> Skin:
    if name not in TEMPLATES:
        raise ValueError(f"unknown template {name!r}; choices: {sorted(TEMPLATES)}")
    return TEMPLATES[name]()
