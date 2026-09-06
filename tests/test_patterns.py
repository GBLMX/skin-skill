"""Tests for decorative patterns (stripes, checker, trim, camouflage)."""

from skinlib import FACES, Skin, apply_pattern, camouflage, checker, stripes

C1 = (240, 60, 60, 255)
C2 = (60, 60, 240, 255)
PALETTE = [(40, 40, 40, 255), (90, 90, 90, 255),
           (140, 140, 140, 255), (200, 200, 200, 255)]


def test_stripes_vertical_alternate_columns():
    s = Skin()
    stripes(s, "head", C1, C2, direction="vertical", width=2)
    x, y, w, h = s.region("head", "base", "front")
    for k, col in enumerate(range(0, w, 2)):
        expected = C1 if k % 2 == 0 else C2
        assert s.img.getpixel((x + col, y)) == expected
        assert s.img.getpixel((x + col, y + h - 1)) == expected  # whole column


def test_stripes_horizontal_alternate_rows():
    s = Skin()
    stripes(s, "head", C1, C2, direction="horizontal", width=2)
    x, y, w, h = s.region("head", "base", "front")
    for k, row in enumerate(range(0, h, 2)):
        expected = C1 if k % 2 == 0 else C2
        assert s.img.getpixel((x, y + row)) == expected
        assert s.img.getpixel((x + w - 1, y + row)) == expected  # whole row


def test_checker_alternates_by_cell():
    s = Skin()
    checker(s, "head", C1, C2, cell=4)
    x, y, _, _ = s.region("head", "base", "front")
    assert s.img.getpixel((x, y)) == C1
    assert s.img.getpixel((x + 4, y)) == C2
    assert s.img.getpixel((x, y + 4)) == C2
    assert s.img.getpixel((x + 4, y + 4)) == C1
    # inside a cell the color is uniform
    assert s.img.getpixel((x + 1, y + 1)) == C1
    assert s.img.getpixel((x + 5, y + 1)) == C2


def test_border_trim_trim_edge_fill_interior():
    s = Skin()
    apply_pattern(s, "border_trim", "head", fill=C1, trim=C2)
    x, y, w, h = s.region("head", "base", "front")
    # the whole 1px perimeter is the trim color
    assert s.img.getpixel((x, y)) == C2
    assert s.img.getpixel((x + w - 1, y)) == C2
    assert s.img.getpixel((x, y + h - 1)) == C2
    assert s.img.getpixel((x + w - 1, y + h - 1)) == C2
    assert s.img.getpixel((x + 1, y)) == C2
    assert s.img.getpixel((x, y + 1)) == C2
    # the interior keeps the fill color
    assert s.img.getpixel((x + 2, y + 2)) == C1
    assert s.img.getpixel((x + w - 3, y + h - 3)) == C1


def test_camouflage_deterministic():
    s1, s2 = Skin(), Skin()
    camouflage(s1, PALETTE, part="head", seed=7)
    camouflage(s2, PALETTE, part="head", seed=7)
    assert s1.img.tobytes() == s2.img.tobytes()


def test_camouflage_fills_region_from_palette():
    s = Skin()
    camouflage(s, PALETTE, part="head", seed=3)
    for face in FACES:
        x, y, w, h = s.region("head", "base", face)
        for i in range(w):
            for j in range(h):
                assert s.img.getpixel((x + i, y + j)) in PALETTE


def _assert_face_fully_painted(skin, part):
    for face in FACES:
        x, y, w, h = skin.region(part, "base", face)
        opaque = sum(1 for i in range(w) for j in range(h)
                     if skin.img.getpixel((x + i, y + j))[3] > 0)
        assert opaque == w * h


def test_every_pattern_fills_the_part():
    makers = [
        lambda s: stripes(s, "head", C1, C2),
        lambda s: checker(s, "head", C1, C2, cell=2),
        lambda s: apply_pattern(s, "border_trim", "head", fill=C1, trim=C2),
        lambda s: camouflage(s, PALETTE, part="head", seed=1),
    ]
    for make in makers:
        s = Skin()
        make(s)
        _assert_face_fully_painted(s, "head")
