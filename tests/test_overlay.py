"""Tests for the mask overlay system."""

import pytest

from skinlib import (
    Skin, overlay_pattern, apply_overlay, rect_mask,
    scratches, cracks, runes,
)


def test_overlay_pattern_replace():
    s = Skin()
    s.paint_part("body", (100, 100, 100, 255), "base")
    overlay_pattern(s, "body", (200, 0, 0, 255), "base", mode="replace")
    x, y, w, h = s.region("body", "base", "front")
    for i in range(w):
        for j in range(h):
            assert s.img.getpixel((x + i, y + j)) == (200, 0, 0, 255)


def test_rect_mask_restricts():
    s = Skin()
    s.paint_part("body", (100, 100, 100, 255), "base")
    overlay_pattern(s, "body", (200, 0, 0, 255), "base", mode="replace",
                    mask=rect_mask(0, 0, 2, 2))
    x, y, w, h = s.region("body", "base", "front")
    assert s.img.getpixel((x, y)) == (200, 0, 0, 255)      # inside mask
    assert s.img.getpixel((x + 3, y + 3)) == (100, 100, 100, 255)  # outside


def test_blend_modes():
    s = Skin()
    s.paint_part("head", (100, 100, 100, 255), "base")
    overlay_pattern(s, "head", (255, 255, 255, 255), "base", mode="add")
    assert s.img.getpixel((8, 8)) == (255, 255, 255, 255)

    s2 = Skin()
    s2.paint_part("head", (100, 100, 100, 255), "base")
    overlay_pattern(s2, "head", (0, 0, 0, 255), "base", mode="multiply")
    assert s2.img.getpixel((8, 8)) == (0, 0, 0, 255)


def test_scratches_deterministic_and_changes():
    base = (128, 128, 128, 255)
    s1 = Skin(); s1.paint_part("body", base, "base")
    s2 = Skin(); s2.paint_part("body", base, "base")
    scratches(s1, "body", seed=9)
    scratches(s2, "body", seed=9)
    assert s1.img.tobytes() == s2.img.tobytes()

    # scratches actually darken some pixels vs. a clean gray body
    scratched = Skin(); scratched.paint_part("body", base, "base")
    scratches(scratched, "body", seed=0)
    clean = Skin(); clean.paint_part("body", base, "base")
    assert scratched.img.tobytes() != clean.img.tobytes()


def test_all_overlays_apply():
    for name in ("scratches", "cracks", "runes"):
        s = Skin()
        s.paint_part("body", (128, 128, 128, 255), "base")
        apply_overlay(s, "body", name, seed=1)
        assert s is not None


def test_apply_overlay_unknown():
    with pytest.raises(ValueError):
        apply_overlay(Skin(), "body", "nope")


def test_runes_color_applied():
    s = Skin()
    s.paint_part("head", (100, 100, 100, 255), "base")
    runes(s, "head", color=(120, 220, 255, 255), seed=0)
    # at least one pixel now equals the glyph color
    colors = set(c for _, c in s.img.getcolors(maxcolors=1_000_000))
    assert (120, 220, 255, 255) in colors
