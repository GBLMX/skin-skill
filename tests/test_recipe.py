"""Tests for the recipe schema and code generator."""

import json

import pytest

from skinlib import Skin, generate_from_recipe, recipe_to_python


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
