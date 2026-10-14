"""Tests for the recipe schema and code generator."""

import json

import pytest

from skinlib import Skin, generate_from_recipe, recipe_to_python
from skinlib.recipe import OPS, _EMITTERS
from skinlib.texture import BLOCK_FACES, Texture


def test_generate_from_recipe_basic():
    recipe = {
        "size": 64, "model": "steve",
        "steps": [
            {"op": "shading", "part": "body", "color": "#78141a", "style": "combined"},
            {"op": "material", "part": "head", "material": "leather"},
        ],
    }
    s = generate_from_recipe(recipe)
    assert isinstance(s, Skin)
    assert s.size == 64


def test_recipe_unknown_op():
    with pytest.raises(ValueError):
        generate_from_recipe({"steps": [{"op": "bogus"}]})


def test_recipe_base_template():
    s = generate_from_recipe({"base": "knight"})
    assert isinstance(s, Skin)


def test_recipe_from_json_file(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"steps": [{"op": "paint", "part": "head", "color": "#ff0000"}]}))
    s = generate_from_recipe(str(p))
    assert s.get_pixel("head", "base", "front", 0, 0) == (255, 0, 0, 255)


def test_recipe_inline_json_string():
    s = generate_from_recipe('{"steps": [{"op": "paint", "part": "body", "color": "#00ff00"}]}')
    assert s.get_pixel("body", "base", "front", 0, 0) == (0, 255, 0, 255)


def test_recipe_to_python_emits_script():
    recipe = {"steps": [{"op": "shading", "part": "body", "color": "#78141a"}]}
    code = recipe_to_python(recipe)
    assert "apply_shading(s" in code
    assert "Skin(" in code


def test_recipe_to_python_runs(tmp_path):
    recipe = {
        "output": str(tmp_path / "out.png"),
        "steps": [{"op": "shading", "part": "body", "color": "#78141a"}],
    }
    code = recipe_to_python(recipe)
    ns = {}
    exec(code, ns)
    assert (tmp_path / "out.png").exists()


def test_recipe_full_pipeline(tmp_path):
    recipe = {
        "size": 64,
        "model": "steve",
        "steps": [
            {"op": "shading", "part": "head", "color": "#f0be96", "style": "combined"},
            {"op": "material", "part": "body", "material": "metal"},
            {"op": "overlay", "part": "body", "overlay": "scratches", "seed": 5},
            {"op": "overlay", "part": "body", "overlay": "runes", "color": "#78dcff"},
        ],
    }
    s = generate_from_recipe(recipe)
    assert isinstance(s, Skin)
    out = tmp_path / "full.png"
    s.save(str(out))
    assert out.exists()


def test_emitter_keys_match_ops():
    assert set(_EMITTERS) == set(OPS)


def test_recipe_to_python_pattern_ops_run_identically():
    recipe = {
        "size": 64,
        "model": "steve",
        "steps": [
            {"op": "pattern", "pattern": "stripes", "part": "body",
             "c1": "#223344", "c2": "#556677",
             "direction": "horizontal", "width": 3},
            {"op": "pattern", "pattern": "camouflage", "part": "head",
             "palette": ["#3b2f23", "#6b5a41", "#8a7a52"], "seed": 7},
        ],
    }
    code = recipe_to_python(recipe)
    assert 'apply_pattern(s, "stripes"' in code
    assert 'apply_pattern(s, "camouflage"' in code
    expected = generate_from_recipe(recipe)
    ns = {}
    exec(code, ns)
    assert ns["s"].img.tobytes() == expected.img.tobytes()


# ---------------------------------------------------------------------------
# Texture recipes: the ``texture`` step is the canvas source
# ---------------------------------------------------------------------------
def test_recipe_texture_block_source():
    t = generate_from_recipe({
        "steps": [
            {"op": "texture", "color": "#2a4d4a", "noise": 4, "seed": 1},
            {"op": "overlay", "part": "all", "overlay": "scratches", "seed": 3},
        ],
    })
    assert isinstance(t, Texture)
    assert t.faces == BLOCK_FACES


def test_recipe_texture_item_icon():
    t = generate_from_recipe({"steps": [
        {"op": "texture", "kind": "item", "shape": "shard", "color": "#8ad2ff"}]})
    assert t.faces == ("front",)
    # the icon archetype leaves a transparent 1px margin
    assert t.get_pixel("all", "base", "front", 0, 0)[3] == 0


def test_recipe_texture_output_dir(tmp_path):
    out = tmp_path / "tex"
    generate_from_recipe({"steps": [{"op": "texture", "color": "#405060"}],
                          "output_dir": str(out)})
    assert sorted(p.name for p in out.glob("*.png")) == [
        "texture_bottom.png", "texture_side.png", "texture_top.png"]


def test_recipe_texture_output_dir_prefix(tmp_path):
    out = tmp_path / "tex"
    generate_from_recipe({"steps": [{"op": "texture", "color": "#405060"}],
                          "output_dir": str(out), "prefix": "stone"})
    assert (out / "stone_top.png").exists()


def test_recipe_texture_skin_ops_rejected():
    for op in ("face", "hair", "band", "decorate"):
        with pytest.raises(ValueError, match="needs a skin canvas"):
            generate_from_recipe({"steps": [
                {"op": "texture", "color": "#112233"},
                {"op": op},
            ]})


def test_recipe_texture_must_come_first():
    with pytest.raises(ValueError, match="must be the first step"):
        generate_from_recipe({"steps": [
            {"op": "paint", "part": "body", "color": "#00ff00"},
            {"op": "texture", "color": "#112233"},
        ]})


def test_recipe_output_dir_needs_a_texture(tmp_path):
    with pytest.raises(ValueError, match="needs a texture recipe"):
        generate_from_recipe({"steps": [{"op": "paint", "part": "body",
                                         "color": "#00ff00"}],
                              "output_dir": str(tmp_path)})


def test_recipe_to_python_texture_runs_identically():
    recipe = {
        "steps": [
            {"op": "texture", "color": [58, 95, 74], "noise": 6, "seed": 2,
             "glow": True, "glow_strength": 0.5, "size": 32},
            {"op": "outline", "part": "all", "color": "#0a0f0c"},
        ],
    }
    code = recipe_to_python(recipe)
    assert "s = block(" in code
    assert "Skin(" not in code
    expected = generate_from_recipe(recipe)
    ns = {}
    exec(code, ns)
    assert isinstance(ns["s"], Texture)
    assert ns["s"].img.tobytes() == expected.img.tobytes()


def test_recipe_to_python_texture_output_dir(tmp_path):
    out = tmp_path / "tex"
    code = recipe_to_python({"steps": [{"op": "texture", "color": "#405060",
                                        "seed": 1}],
                             "output_dir": str(out)})
    ns = {}
    exec(code, ns)
    assert (out / "texture_top.png").exists()


def test_recipe_texture_named_source():
    pytest.importorskip("minebase")
    t = generate_from_recipe({"steps": [
        {"op": "texture", "name": "sculk_sensor", "color": "#2a4d4a",
         "noise": 4, "seed": 1}]})
    assert isinstance(t, Texture)
