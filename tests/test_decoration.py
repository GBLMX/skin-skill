"""Tests for 3D decoration: hat, jacket/pants overlays, depth accents."""

from skinlib import (
    Skin, add_highlights, add_shadows, apply_3d_decoration,
    hat, jacket_front, pants_outline, shade,
)


def test_hat_covers_head_top_with_weave():
    s = Skin()
    color = (120, 60, 40, 255)
    top = (210, 140, 90, 255)
    hat(s, color, top_color=top)
    x, y, w, h = s.region("head", "overlay", "top")
    # weave alternates a shaded tone with the plain top color
    assert s.img.getpixel((x, y)) == shade(top, 0.85)
    assert s.img.getpixel((x + 1, y)) == top
    assert s.img.getpixel((x, y + 1)) == top
    assert s.img.getpixel((x + 1, y + 1)) == shade(top, 0.85)
    # the whole top face is painted (nothing transparent remains)
    assert s.img.getpixel((x + w - 1, y + h - 1)) in (top, shade(top, 0.85))


def test_hat_rim_covers_top_rows_face_stays_clear():
    s = Skin()
    color = (120, 60, 40, 255)
    s.paint_part("head", (190, 150, 120, 255))
    hat(s, color, top_color=color)
    x, y, _, _ = s.region("head", "overlay", "front")
    # scale 1: the rim is the top three logical rows
    for v in range(3):
        assert s.img.getpixel((x + 4, y + v)) == color
    # below the rim the overlay is transparent, so the face shows through
    assert s.img.getpixel((x + 4, y + 3))[3] == 0


def test_jacket_front_center_zipper_with_highlights():
    s = Skin()
    s.paint_part("body", (140, 140, 140, 255))
    color = (40, 40, 160, 255)
    hi = (255, 255, 255, 255)
    jacket_front(s, color, highlight=hi)
    x, y, w, h = s.region("body", "overlay", "front")
    mid = x + w // 2
    dark = shade(color, 0.7)
    for v in range(3, 9):
        assert s.img.getpixel((mid, y + v)) == dark  # center zipper column
    for v in (3, 5, 7):
        assert s.img.getpixel((mid + 1, y + v)) == hi  # bright highlight
    # sparse: the overlay stays transparent above and below the zipper
    assert s.img.getpixel((mid, y + 2))[3] == 0
    assert s.img.getpixel((mid, y + 9))[3] == 0
    assert h >= 10  # sampled rows sit inside the front face


def test_pants_outline_hem_and_highlight():
    s = Skin()
    color = (60, 40, 120, 255)
    hi = (255, 255, 255, 255)
    pants_outline(s, color, highlight=hi)
    for leg in ("right_leg", "left_leg"):
        x, y, w, h = s.region(leg, "overlay", "front")
        # bottom hem: the last two rows
        for i in range(w):
            assert s.img.getpixel((x + i, y + h - 2)) == color
            assert s.img.getpixel((x + i, y + h - 1)) == shade(color, 0.7)
        # highlight row just above the hem, between the outer edges
        for i in range(1, w - 1):
            assert s.img.getpixel((x + i, y + h - 3)) == hi
        assert s.img.getpixel((x, y + h - 3))[3] == 0
        assert s.img.getpixel((x + w - 1, y + h - 3))[3] == 0
        assert s.img.getpixel((x, y + h - 4))[3] == 0


def test_add_highlights_at_custom_positions():
    s = Skin()
    base = (120, 120, 120, 255)
    s.paint_part("body", base)
    highlight = (255, 255, 255, 255)
    add_highlights(s, "body", highlight, positions=[(1, 1), (6, 10)])
    x, y, _, _ = s.region("body", "base", "front")
    assert s.img.getpixel((x + 1, y + 1)) == highlight
    assert s.img.getpixel((x + 6, y + 10)) == highlight
    # neighbouring pixels are left alone
    assert s.img.getpixel((x + 2, y + 1)) == base
    assert s.img.getpixel((x + 6, y + 9)) == base


def test_add_shadows_bottom_row_and_side_edges():
    s = Skin()
    base = (200, 160, 90, 255)
    s.paint_part("head", base)
    shadow = (60, 40, 20, 255)
    add_shadows(s, "head", shadow)
    x, y, w, h = s.region("head", "base", "front")
    bottom = shade(shadow, 0.6)
    edge = shade(shadow, 0.6 * 0.9)
    # bottom row interior: bottom shadow; corners: overwritten by the side
    # edge pass (last write wins), so they take the edge color
    for i in range(1, w - 1):
        assert s.img.getpixel((x + i, y + h - 1)) == bottom
    for j in range(h):
        assert s.img.getpixel((x, y + j)) == edge  # left edge (incl. corners)
        assert s.img.getpixel((x + w - 1, y + j)) == edge  # right edge
    # the interior is untouched
    assert s.img.getpixel((x + w // 2, y + h // 2)) == base


def test_apply_3d_decoration_paints_overlay_layers():
    s = Skin()
    apply_3d_decoration(
        s,
        hat_color=(120, 60, 40, 255),
        jacket_color=(40, 40, 160, 255),
        pants_color=(60, 40, 120, 255),
    )
    # hat: the head top overlay is fully painted
    x, y, w, h = s.region("head", "overlay", "top")
    assert sum(1 for i in range(w) for j in range(h)
               if s.img.getpixel((x + i, y + j))[3] > 0) == w * h
    # jacket: dark zipper pixels appear on the body front overlay
    bx, by, bw, _ = s.region("body", "overlay", "front")
    assert s.img.getpixel((bx + bw // 2, by + 3))[3] == 255
    assert s.img.getpixel((bx + bw // 2, by + 8))[3] == 255
    # pants: the bottom hem appears on both legs
    for leg in ("right_leg", "left_leg"):
        lx, ly, _, lh = s.region(leg, "overlay", "front")
        assert s.img.getpixel((lx, ly + lh - 1))[3] == 255
        assert s.img.getpixel((lx, ly + lh - 2))[3] == 255
