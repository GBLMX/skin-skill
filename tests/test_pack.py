"""Tests for the resource pack writer."""

import json
import zipfile

import pytest

from skinlib.pack import build_pack, pack_format, pack_meta
from skinlib.texture import block, icon

SCULK = (42, 77, 74, 255)


def test_pack_format_matches_the_table():
    assert pack_format("1.21.6") == 63
    assert pack_format("1.21.7") == 64
    assert pack_format("1.21") == 34
    assert pack_format("1.20.2") == 18
    assert pack_format("1.13") == 4
    assert pack_format("1.21.9") == 69.0
    assert pack_format("26.2") == 88.0


def test_pack_format_unknown_versions_raise():
    for version in ("25w31a", "1.22", "1.21.6-rc1", "", "nonsense"):
        with pytest.raises(ValueError):
            pack_format(version)


def test_pack_meta_shape_follows_the_version():
    assert pack_meta("1.21.6")["pack"]["pack_format"] == 63
    pack = pack_meta("1.21.9")["pack"]
    assert pack["min_format"] == 69.0 and pack["max_format"] == 69.0
    assert "pack_format" not in pack


def test_pack_meta_explicit_format_for_a_snapshot():
    # an unparseable version cannot tell us the shape, so it gets the legacy field
    assert pack_meta("25w31a", 63)["pack"]["pack_format"] == 63


def test_build_pack_directory_layout(tmp_path):
    out = tmp_path / "pack"
    build_pack(out, blocks={"sculk": block(SCULK)},
               items={"sculk_shard": icon((138, 210, 255, 255), shape="shard")},
               version="1.21.6")
    assert json.loads((out / "pack.mcmeta").read_text())["pack"]["pack_format"] == 63

    ns = out / "assets" / "minecraft"
    for face in ("top", "side", "bottom"):
        assert (ns / "textures" / "block" / f"sculk_{face}.png").exists()
    assert (ns / "textures" / "item" / "sculk_shard.png").exists()

    model = json.loads((ns / "models" / "block" / "sculk.json").read_text())
    assert model["parent"] == "minecraft:block/cube"
    assert model["textures"]["up"] == "minecraft:block/sculk_top"
    assert model["textures"]["north"] == "minecraft:block/sculk_side"
    assert model["textures"]["particle"] == "minecraft:block/sculk_side"

    state = json.loads((ns / "blockstates" / "sculk.json").read_text())
    assert state["variants"][""]["model"] == "minecraft:block/sculk"

    item = json.loads((ns / "models" / "item" / "sculk_shard.json").read_text())
    assert item["parent"] == "minecraft:item/generated"
    assert item["textures"]["layer0"] == "minecraft:item/sculk_shard"


def test_build_pack_namespace(tmp_path):
    out = tmp_path / "pack"
    build_pack(out, blocks={"ore": block((90, 90, 90, 255))}, namespace="mypack",
               version="1.21.6")
    model = json.loads(
        (out / "assets" / "mypack" / "models" / "block" / "ore.json").read_text())
    assert model["textures"]["up"] == "mypack:block/ore_top"
    assert (out / "assets" / "mypack" / "blockstates" / "ore.json").exists()
    assert not (out / "assets" / "minecraft").exists()


def test_build_pack_single_face_block_uses_cube_all(tmp_path):
    out = tmp_path / "pack"
    build_pack(out, blocks={"panel": block((10, 20, 30, 255), faces=("front",))},
               version="1.21.6")
    model = json.loads(
        (out / "assets" / "minecraft" / "models" / "block" / "panel.json").read_text())
    assert model["parent"] == "minecraft:block/cube_all"
    assert model["textures"]["all"] == "minecraft:block/panel_front"
    assert (out / "assets" / "minecraft" / "textures" / "block"
            / "panel_front.png").exists()


def test_build_pack_rejects_unknown_face_shapes(tmp_path):
    with pytest.raises(ValueError, match="knows the cube set"):
        build_pack(tmp_path / "pack",
                   blocks={"weird": block((1, 2, 3, 255), faces=("top", "side"))},
                   version="1.21.6")


def test_build_pack_rejects_multi_face_items(tmp_path):
    with pytest.raises(ValueError, match="single sprite"):
        build_pack(tmp_path / "pack", items={"weird": block((1, 2, 3, 255))},
                   version="1.21.6")


def test_build_pack_zip_puts_mcmeta_at_the_root(tmp_path):
    out = tmp_path / "pack.zip"
    build_pack(out, blocks={"sculk": block(SCULK)}, version="1.21.6")
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert "pack.mcmeta" in names
        assert "assets/minecraft/textures/block/sculk_top.png" in names
        assert "assets/minecraft/models/block/sculk.json" in names
        assert json.loads(zf.read("pack.mcmeta"))["pack"]["pack_format"] == 63
        assert not [n for n in names if n.startswith("/")]


def test_build_pack_needs_something_to_write(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        build_pack(tmp_path / "pack", version="1.21.6")


def test_build_pack_needs_a_version_or_format(tmp_path):
    with pytest.raises(ValueError, match="version="):
        build_pack(tmp_path / "pack", blocks={"a": block(SCULK)})


def test_build_pack_every_texture_ref_resolves(tmp_path):
    """The invariant that keeps a pack from rendering purple and black."""
    out = tmp_path / "pack.zip"
    build_pack(out,
               blocks={"cube": block(SCULK),
                       "panel": block((9, 9, 9, 255), faces=("front",))},
               items={"shard": icon((1, 2, 3, 255), shape="shard")},
               version="1.21.6")
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        for name in ("cube", "panel"):
            assert f"assets/minecraft/models/block/{name}.json" in names
            assert f"assets/minecraft/blockstates/{name}.json" in names
        assert "assets/minecraft/models/item/shard.json" in names
        for name in sorted(n for n in names if "/models/" in n):
            for ref in json.loads(zf.read(name)).get("textures", {}).values():
                namespace, _, path = ref.partition(":")
                assert f"assets/{namespace}/textures/{path}.png" in names, (name, ref)
