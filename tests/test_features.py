"""Tests for character features: face details, 3D hair, wrap bands."""

from skinlib import Skin, band, face, hair


def test_face_eye_pixels_opaque_on_blank_head():
    s = Skin()
    eye = (0, 60, 255, 255)
    hot = (140, 220, 255, 255)
    face(s, eye_color=eye, eye_hot=hot)
    # eyes sit at logical (u=1, v=4) and (u=6, v=4); the glint at (2, 4)
    assert s.get_pixel("head", "base", "front", 1, 4) == eye
    assert s.get_pixel("head", "base", "front", 6, 4) == eye
    assert s.get_pixel("head", "base", "front", 2, 4) == hot


def test_face_draws_brows_nose_mouth_chin():
    s = Skin()
    s.paint_part("head", (200, 150, 120, 255))
    brow = (60, 50, 40, 255)
    mouth = (255, 60, 60, 255)
    nose = (120, 90, 70, 255)
    face(s, brow_color=brow, mouth_color=mouth, nose_shade=nose)
    assert s.get_pixel("head", "base", "front", 1, 3) == brow
    assert s.get_pixel("head", "base", "front", 6, 3) == brow
    assert s.get_pixel("head", "base", "front", 3, 5) == nose
    assert s.get_pixel("head", "base", "front", 4, 6) == mouth
    assert s.get_pixel("head", "base", "front", 3, 7) == nose


def test_hair_covers_top_rows_keeps_lower_face():
    s = Skin()
    skin_tone = (200, 150, 120, 255)
    hair_color = (60, 40, 25, 255)
    s.paint_part("head", skin_tone)
    hair(s, hair_color)
    # top rows of the head are covered on front (fringe) and side faces
    assert s.get_pixel("head", "base", "front", 3, 0) == hair_color
    assert s.get_pixel("head", "overlay", "front", 3, 0) == hair_color
    assert s.get_pixel("head", "base", "right", 2, 1) == hair_color
    assert s.get_pixel("head", "overlay", "right", 2, 2) == hair_color
    # the lower half of the head keeps the skin tone visible
    assert s.get_pixel("head", "base", "front", 3, 4) == skin_tone
    assert s.get_pixel("head", "base", "front", 3, 7) == skin_tone
    assert s.get_pixel("head", "base", "right", 4, 5) == skin_tone


def test_band_covers_v0_to_v1_rows_only():
    s = Skin()
    color = (210, 80, 40, 255)
    dark = (90, 20, 0, 255)
    band(s, "head", 4, 5, color, dark=dark)
    for f in ("front", "right", "back", "left"):
        assert s.get_pixel("head", "overlay", f, 3, 3)[3] == 0  # above band
        assert s.get_pixel("head", "overlay", f, 0, 4) == color
        assert s.get_pixel("head", "overlay", f, 7, 4) == color
        assert s.get_pixel("head", "overlay", f, 3, 5) == dark  # last row darker
        assert s.get_pixel("head", "overlay", f, 3, 6)[3] == 0  # below band


def test_band_scale_on_128px_skin():
    s = Skin(size=128)
    color = (210, 80, 40, 255)
    dark = (90, 20, 0, 255)
    band(s, "head", 2, 3, color, dark=dark)
    # logical coordinates stay 64px-based on 128px skins
    assert s.get_pixel("head", "overlay", "front", 4, 1)[3] == 0
    assert s.get_pixel("head", "overlay", "front", 4, 2) == color
    assert s.get_pixel("head", "overlay", "front", 4, 3) == dark
    assert s.get_pixel("head", "overlay", "front", 4, 4)[3] == 0
    # each logical band row expands to a 2px-tall block (not a single row)
    x, y, _, _ = s.region("head", "overlay", "front")
    sc = s.scale
    assert s.img.getpixel((x + 4 * sc, y + 2 * sc + 1)) == color
    assert s.img.getpixel((x + 4 * sc, y + 3 * sc + 1)) == dark


def test_features_deterministic():
    s1, s2 = Skin(), Skin()
    face(s1, eye_color=(0, 60, 255, 255), eye_hot=(140, 220, 255, 255))
    face(s2, eye_color=(0, 60, 255, 255), eye_hot=(140, 220, 255, 255))
    assert s1.img.tobytes() == s2.img.tobytes()

    s1, s2 = Skin(), Skin()
    hair(s1, (60, 40, 25, 255))
    hair(s2, (60, 40, 25, 255))
    assert s1.img.tobytes() == s2.img.tobytes()

    s1, s2 = Skin(), Skin()
    band(s1, "head", 3, 4, (200, 40, 40, 255))
    band(s2, "head", 3, 4, (200, 40, 40, 255))
    assert s1.img.tobytes() == s2.img.tobytes()
