"""Preset character templates built with the shading API."""

from __future__ import annotations

from .model import Skin
from .shading import apply_shading


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


TEMPLATES = {
    "knight": knight,
    "villager": villager,
    "astronaut": astronaut,
}


def build_template(name: str) -> Skin:
    if name not in TEMPLATES:
        raise ValueError(f"unknown template {name!r}; choices: {sorted(TEMPLATES)}")
    return TEMPLATES[name]()
