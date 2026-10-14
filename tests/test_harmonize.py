"""Tests for harmonize -- matching a texture's colors to a reference image.

The two modes exist because a shaded skin and a flat logo want different
things, so the assertions here are mostly about what each mode is *allowed* to
change: ``retheme`` may not touch lightness, ``palette`` may.
"""

import pytest
from PIL import Image

from skinlib.harmonize import (MODES, color_difference, delta_e, harmonize,
                               harmonize_report, lab_to_rgb, region_mask,
                               rgb_to_lab)


def _img(colors, size=4):
    """A ``size`` x ``size`` RGBA image painted row by row from ``colors``."""
    im = Image.new("RGBA", (size, size))
    px = im.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = colors[(y * size + x) % len(colors)]
    return im


# Four steps of one sage ramp: a hand-shaded skin in miniature.
RAMP = [(200, 205, 180, 255), (150, 155, 130, 255),
        (100, 104, 86, 255), (52, 56, 44, 255)]
# Dark teal family, the kind of palette a cape provides.
DARK_TEAL = [(0, 16, 16, 255), (0, 64, 80, 255), (32, 208, 224, 255)]


def _pixels(im):
    px = im.convert("RGBA").load()
    return [px[x, y] for y in range(im.height) for x in range(im.width)]


def _labs(im):
    return [rgb_to_lab(p) for p in _pixels(im)]


# ---------------------------------------------------------------------------
# Color space
# ---------------------------------------------------------------------------
def test_lab_round_trip_survives_the_middle_gamut():
    for color in [(0, 0, 0), (255, 255, 255), (12, 150, 200),
                  (240, 190, 150), (30, 60, 90)]:
        assert lab_to_rgb(rgb_to_lab(color))[:3] == pytest.approx(color, abs=1)


def test_delta_e_is_zero_for_identical_and_grows_with_distance():
    base = rgb_to_lab((120, 20, 25))
    assert delta_e(base, base) == 0.0
    assert delta_e(base, rgb_to_lab((220, 120, 125))) > delta_e(
        base, rgb_to_lab((140, 30, 35)))


# ---------------------------------------------------------------------------
# The two modes
# ---------------------------------------------------------------------------
def test_retheme_keeps_the_lightness_ramp_but_moves_the_color():
    target, ref = _img(RAMP), _img(DARK_TEAL)
    out = harmonize(target, ref, mode="retheme")
    moved = 0.0
    for before, after in zip(_labs(target), _labs(out)):
        assert abs(after[0] - before[0]) < 2.0      # the shading step survives
        moved = max(moved, delta_e(before, after))
    assert moved > 10.0                             # the color really changed


def test_palette_mode_collapses_the_ramp():
    original = _labs(_img(RAMP))
    retheme = _labs(harmonize(_img(RAMP), _img(DARK_TEAL), mode="retheme"))
    palette = _labs(harmonize(_img(RAMP), _img(DARK_TEAL), mode="palette"))
    held = max(abs(a[0] - o[0]) for a, o in zip(retheme, original))
    lost = max(abs(a[0] - o[0]) for a, o in zip(palette, original))
    assert held < 2.0 < lost


def test_palette_mode_lands_on_the_reference_palette():
    out = harmonize(_img(RAMP), _img(DARK_TEAL), mode="palette")
    assert color_difference(out, _img(DARK_TEAL)) == pytest.approx(0.0, abs=0.5)


def test_reference_colors_are_used_exactly_not_binned():
    # Binning to 16 levels would turn this into (240, 240, 144).
    ref = _img([(253, 251, 154, 255)])
    target = _img([(200, 205, 180, 255)])
    assert harmonize(target, ref, mode="palette").getpixel((0, 0))[:3] == (253, 251, 154)
    report = harmonize_report(target, ref, mode="palette")
    assert report["reference_palette"] == [(253, 251, 154, 255)]


def test_strength_zero_is_a_no_op_and_one_goes_all_the_way():
    target, ref = _img(RAMP), _img(DARK_TEAL)
    untouched = harmonize(target, ref, strength=0.0)
    assert [p[:3] for p in _pixels(untouched)] == pytest.approx(
        [p[:3] for p in _pixels(target)], abs=1)
    half = harmonize(target, ref, mode="palette", strength=0.5)
    full = harmonize(target, ref, mode="palette", strength=1.0)
    assert color_difference(half, ref) > color_difference(full, ref)


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError, match="unknown mode"):
        harmonize(_img(RAMP), _img(DARK_TEAL), mode="nearest")
    assert MODES == ("retheme", "palette")


# ---------------------------------------------------------------------------
# Edges: masking, alpha, sizes
# ---------------------------------------------------------------------------
def test_mask_confines_the_change_to_the_selection():
    target = _img([(200, 205, 180, 255)] * 16)
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((0, 0), 255)
    out = harmonize(target, _img([(0, 64, 80, 255)]), mask=mask)
    assert out.getpixel((0, 0)) != target.getpixel((0, 0))
    assert out.getpixel((3, 3)) == target.getpixel((3, 3))


def test_transparent_pixels_are_left_alone():
    target = _img([(200, 205, 180, 255), (200, 205, 180, 0)])
    out = harmonize(target, _img(DARK_TEAL))
    assert out.getpixel((1, 0)) == target.getpixel((1, 0))   # colors[1] is clear
    assert out.getpixel((0, 0))[3] == 255                    # opaque stays opaque
    assert out.getpixel((0, 0)) != target.getpixel((0, 0))


def test_reference_may_differ_in_size_from_the_target():
    target = _img([(200, 205, 180, 255)], size=4)
    ref = _img([(0, 64, 80, 255)], size=8)
    out = harmonize(target, ref, mode="palette")
    assert out.size == (4, 4)                                # the target's size wins
    assert color_difference(out, ref) == pytest.approx(0.0, abs=0.5)


# ---------------------------------------------------------------------------
# Report and region masks
# ---------------------------------------------------------------------------
def test_report_exposes_comparable_before_and_after():
    report = harmonize_report(_img(RAMP), _img(DARK_TEAL), mode="palette")
    assert report["delta_before"] > 0
    assert report["delta_after"] < report["delta_before"]
    assert report["mode"] == "palette"
    assert report["image"].size == (4, 4)
    assert report["target_palette"] and report["reference_palette"]


def test_report_measures_both_ends_inside_the_mask():
    target, ref = _img(RAMP), _img(DARK_TEAL)
    mask = Image.new("L", (4, 4), 0)
    for y in range(2):
        for x in range(2):
            mask.putpixel((x, y), 255)
    report = harmonize_report(target, ref, mask=mask)
    assert report["delta_before"] == pytest.approx(
        color_difference(target, ref, mask=mask))


def test_region_mask_selects_parts_layers_and_faces():
    front = region_mask("steve", 64, parts=("body",), layers=("base",),
                        faces=("front",))
    assert front.size == (64, 64)
    assert front.getpixel((23, 25)) == 255        # body base front
    assert front.getpixel((23, 41)) == 0          # same face, but the overlay
    assert front.getpixel((35, 25)) == 0          # same layer and part, the back
    assert front.getpixel((11, 11)) == 0          # the head is not the body


def test_region_mask_defaults_to_everything():
    every = region_mask("steve", 64)
    assert every.getpixel((23, 25)) == 255        # body base front
    assert every.getpixel((11, 11)) == 255        # head base front
    assert every.getpixel((0, 0)) == 0            # this corner is unused skin


def test_region_mask_rejects_unknown_names_and_sizes():
    with pytest.raises(ValueError, match="unknown part"):
        region_mask("steve", 64, parts=("tentacle",))
    with pytest.raises(ValueError, match="unknown face"):
        region_mask("steve", 64, faces=("sideways",))
    with pytest.raises(ValueError, match="size"):
        region_mask("steve", 32)


def test_region_mask_follows_the_alex_model():
    narrow = region_mask("alex", 64, parts=("left_arm",), layers=("base",),
                         faces=("front",))
    wide = region_mask("steve", 64, parts=("left_arm",), layers=("base",),
                       faces=("front",))
    assert narrow.getpixel((38, 52)) == 255       # alex's arm is three wide
    assert narrow.getpixel((39, 52)) == 0
    assert wide.getpixel((39, 52)) == 255         # steve's is four
