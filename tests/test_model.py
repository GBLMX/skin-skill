"""Tests for the core data model: UV layouts, color parsing, model detection."""

import pytest
from PIL import Image

from skinlib import Skin, create, parse_color
from skinlib.model import (
    SteveLayout, make_layout, detect_model, legacy_to_modern,
    PARTS, LAYERS, FACES,
)


def test_layout_has_all_regions():
    layout = make_layout("steve")
    for part in PARTS:
        for layer in LAYERS:
            for face in FACES:
                assert layout[part][layer][face] is not None


def test_head_front_box():
    b = SteveLayout["head"]["base"]["front"]
    assert (b.x, b.y, b.w, b.h) == (8, 8, 8, 8)


def test_alex_slim_arms():
    assert make_layout("alex")["right_arm"]["base"]["front"].w == 3
    assert make_layout("alex")["left_arm"]["base"]["front"].w == 3
    assert make_layout("steve")["right_arm"]["base"]["front"].w == 4


def test_parse_color():
    assert parse_color("240,190,150") == (240, 190, 150, 255)
    assert parse_color("1,2,3,4") == (1, 2, 3, 4)
    assert parse_color("#ff0000") == (255, 0, 0, 255)
    assert parse_color("#ff000080") == (255, 0, 0, 128)
    with pytest.raises(ValueError):
        parse_color("nonsense")


def test_create_size_model():
    assert create(size=64).img.size == (64, 64)
    assert create(size=128).img.size == (128, 128)
    with pytest.raises(ValueError):
        create(size=32)


def test_region_scaling_128():
    s = Skin(size=128)
    x, y, w, h = s.region("head", "base", "front")
    assert (w, h) == (16, 16)  # 8 logical px * scale 2


def test_pixel_roundtrip_and_bounds():
    s = create()
    s.pixel("head", "base", "front", 0, 0, (255, 0, 0, 255))
    assert s.get_pixel("head", "base", "front", 0, 0) == (255, 0, 0, 255)
    with pytest.raises(ValueError):
        s.pixel("head", "base", "front", 8, 0, (0, 0, 0, 255))


def test_detect_model():
    steve = Skin(size=64, model="steve")
    steve.paint_part("right_arm", (255, 255, 255, 255), "base")
    assert detect_model(steve.img) == "steve"

    alex = Skin(size=64, model="alex")
    alex.paint_part("right_arm", (255, 255, 255, 255), "base")
    assert detect_model(alex.img) == "alex"


def test_legacy_to_modern():
    legacy = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    legacy.paste(Image.new("RGBA", (16, 16), (255, 0, 0, 255)), (40, 16))
    modern = legacy_to_modern(legacy)
    assert modern.size == (64, 64)
    assert modern.getpixel((44, 20)) == (255, 0, 0, 255)  # right arm kept
    assert modern.getpixel((36, 52)) == (255, 0, 0, 255)  # mirrored to left arm


def test_save_load_roundtrip(tmp_path):
    s = create()
    s.paint_part("head", (240, 190, 150, 255), "base")
    p = tmp_path / "s.png"
    s.save(str(p))
    s2 = Skin.load(str(p), model="steve")
    assert s2.img.getpixel((8, 8)) == (240, 190, 150, 255)
