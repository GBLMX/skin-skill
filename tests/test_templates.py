"""Tests for style profiles and preset templates."""

import pytest

from skinlib import (
    Skin, build_template, TEMPLATES, apply_style, STYLE_PROFILES, CLOTHING,
)


def test_templates_registry():
    assert {"knight", "villager", "astronaut",
            "noob", "herobrine", "medieval_knight"} <= set(TEMPLATES)


def test_all_templates_build():
    for name in TEMPLATES:
        assert isinstance(build_template(name), Skin)


def test_style_profiles_registry():
    assert {"minimal", "clean", "metal", "mottled", "leathery"} <= set(STYLE_PROFILES)


def test_apply_style_all_profiles():
    for profile in STYLE_PROFILES:
        s = Skin()
        apply_style(s, "body", (100, 100, 100, 255), profile)
        x, y, w, h = s.region("body", "base", "front")
        assert s.img.getpixel((x, y))[3] > 0


def test_apply_style_minimal_is_flat():
    s = Skin()
    apply_style(s, "body", (100, 100, 100, 255), "minimal")
    x, y, w, h = s.region("body", "base", "front")
    for i in range(w):
        for j in range(h):
            assert s.img.getpixel((x + i, y + j)) == (100, 100, 100, 255)


def test_apply_style_mottled_differs_from_minimal():
    base = (100, 100, 100, 255)
    s1 = Skin(); apply_style(s1, "body", base, "minimal")
    s2 = Skin(); apply_style(s2, "body", base, "mottled")
    assert s1.img.tobytes() != s2.img.tobytes()


def test_apply_style_unknown():
    with pytest.raises(ValueError):
        apply_style(Skin(), "body", (1, 2, 3, 255), "nope")


def test_noob_gray_body():
    s = build_template("noob")
    assert s.get_pixel("body", "base", "front", 0, 0) == CLOTHING["gray"]


def test_herobrine_white_eyes():
    s = build_template("herobrine")
    assert s.get_pixel("head", "base", "front", 1, 4) == (255, 255, 255, 255)
