"""Recipe schema: build a skin from a declarative, JSON-serializable recipe.

A recipe is a small JSON document that lists the operations to apply, so an AI
agent (or a user) can describe a skin declaratively instead of writing Python.
The library executes it deterministically — no LLM call lives in this package.

Recipe shape::

    {
      "size": 64,               # optional, default 64 (64 | 128)
      "model": "steve",         # optional, default "steve" ("steve" | "alex")
      "base": "knight",         # optional template to start from
      "steps": [
        {"op": "shading", "part": "body", "color": "#78141a", "style": "artistic"},
        {"op": "material", "part": "body", "material": "leather"},
        {"op": "overlay", "part": "body", "overlay": "scratches", "seed": 3},
        {"op": "pixel", "part": "head", "layer": "overlay", "face": "front",
         "u": 1, "v": 1, "color": "#ff0000"}
      ],
      "output": "skin.png",     # optional save path
      "render": {...}           # optional (unused by generate_from_recipe)
    }

Colors may be written as ``"R,G,B"`` / ``"R,G,B,A"`` / ``"#RRGGBB"`` strings or
as ``[r, g, b]`` / ``[r, g, b, a]`` lists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict

from .model import Skin, parse_color
from .shading import apply_shading, outline
from .patterns import apply_pattern
from .materials import apply_material
from .overlay import apply_overlay
from .decoration import apply_3d_decoration
from .features import face, hair, band
from .templates import build_template


def _col(v: Any) -> tuple:
    if isinstance(v, str):
        return parse_color(v)
    return tuple(v)


def _maybe_col(v: Any):
    return _col(v) if v is not None else None


# ---------------------------------------------------------------------------
# Op executors: (skin, params) -> skin
# ---------------------------------------------------------------------------
def _op_shading(s: Skin, p: dict) -> Skin:
    apply_shading(s, p["part"], _col(p["color"]), p.get("layer", "base"),
                  style=p.get("style", "combined"),
                  noise=p.get("noise", False),
                  noise_var=p.get("noise_var", 6),
                  seed=p.get("seed", 0))
    return s


def _op_material(s: Skin, p: dict) -> Skin:
    apply_material(s, p["part"], p["material"],
                   color=_maybe_col(p.get("color")),
                   layer=p.get("layer", "base"),
                   seed=p.get("seed"))
    return s


def _op_pattern(s: Skin, p: dict) -> Skin:
    name = p["pattern"]
    layer = p.get("layer", "base")
    if name == "camouflage":
        pal = [_col(c) for c in p.get("palette", [])]
        apply_pattern(s, "camouflage", pal, part=p["part"], layer=layer,
                      seed=p.get("seed", 0))
    elif name == "stripes":
        apply_pattern(s, "stripes", p["part"], _col(p["c1"]), _col(p["c2"]),
                      layer=layer, direction=p.get("direction", "vertical"),
                      width=p.get("width", 2))
    elif name == "checker":
        apply_pattern(s, "checker", p["part"], _col(p["c1"]), _col(p["c2"]),
                      layer=layer, cell=p.get("cell", 4))
    elif name == "border_trim":
        apply_pattern(s, "border_trim", p["part"], _col(p["c1"]), _col(p["c2"]),
                      layer=layer, width=p.get("width", 1))
    else:
        raise ValueError(f"unknown pattern {name!r}")
    return s


def _op_overlay(s: Skin, p: dict) -> Skin:
    kw: dict = {"layer": p.get("layer", "base"), "seed": p.get("seed", 0)}
    if p.get("color"):
        kw["color"] = _col(p["color"])
    apply_overlay(s, p["part"], p["overlay"], **kw)
    return s


def _op_decorate(s: Skin, p: dict) -> Skin:
    apply_3d_decoration(
        s,
        hat_color=_maybe_col(p.get("hat")),
        jacket_color=_maybe_col(p.get("jacket")),
        pants_color=_maybe_col(p.get("pants")),
    )
    return s


def _op_face(s: Skin, p: dict) -> Skin:
    face(s,
         eye_color=_maybe_col(p.get("eyes")) or (96, 226, 140, 255),
         brow_color=_maybe_col(p.get("brows")) or (120, 110, 105, 255),
         mouth_color=_maybe_col(p.get("mouth")) or (110, 92, 88, 255))
    return s


def _op_hair(s: Skin, p: dict) -> Skin:
    hair(s, _col(p["color"]),
         light=_maybe_col(p.get("light")),
         dark=_maybe_col(p.get("dark")))
    return s


def _op_band(s: Skin, p: dict) -> Skin:
    band(s, p["part"], p["v0"], p["v1"], _col(p["color"]),
         layer=p.get("layer", "overlay"))
    return s


def _op_outline(s: Skin, p: dict) -> Skin:
    outline(s, p["part"], _col(p["color"]),
            layer=p.get("layer", "base"), width=p.get("width", 1))
    return s


def _op_pixel(s: Skin, p: dict) -> Skin:
    s.pixel(p["part"], p.get("layer", "base"), p["face"], p["u"], p["v"],
            _col(p["color"]))
    return s


def _op_paint(s: Skin, p: dict) -> Skin:
    if p.get("face"):
        s.paint_face(p["part"], p.get("layer", "base"), p["face"], _col(p["color"]))
    else:
        s.paint_part(p["part"], _col(p["color"]), p.get("layer", "base"))
    return s


OPS: Dict[str, Callable[[Skin, dict], Skin]] = {
    "shading": _op_shading,
    "material": _op_material,
    "pattern": _op_pattern,
    "overlay": _op_overlay,
    "decorate": _op_decorate,
    "face": _op_face,
    "hair": _op_hair,
    "band": _op_band,
    "outline": _op_outline,
    "pixel": _op_pixel,
    "paint": _op_paint,
}


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def generate_from_recipe(recipe, output: str = None) -> Skin:
    """Build a skin from a recipe (dict, JSON string, or path to a JSON file).

    Returns the resulting Skin (saved to ``output`` if given).
    """
    if isinstance(recipe, (str, Path)):
        text = recipe if not Path(recipe).exists() else Path(recipe).read_text(encoding="utf-8")
        recipe = json.loads(text)

    base = recipe.get("base")
    if base:
        s = build_template(base)
    else:
        s = Skin(size=recipe.get("size", 64), model=recipe.get("model", "steve"))

    for step in recipe.get("steps", []):
        op = step.get("op")
        if op not in OPS:
            raise ValueError(f"unknown op {op!r}; choices: {sorted(OPS)}")
        s = OPS[op](s, step)

    out = output or recipe.get("output")
    if out:
        s.save(out)
    return s


# ---------------------------------------------------------------------------
# Codegen (emit an imperative Python script from a recipe)
# ---------------------------------------------------------------------------
def _crepr(v: Any) -> str:
    return repr(tuple(_col(v)))


def _emit(step: dict) -> str:
    op = step["op"]
    p = step
    if op == "shading":
        return (f'apply_shading(s, {p["part"]!r}, {_crepr(p["color"])}, '
                f'{p.get("layer", "base")!r}, style={p.get("style", "combined")!r}, '
                f'noise={p.get("noise", False)!r}, seed={p.get("seed", 0)!r})')
    if op == "material":
        color = f', color={_crepr(p["color"])}' if p.get("color") else ""
        return (f'apply_material(s, {p["part"]!r}, {p["material"]!r}'
                f'{color}, layer={p.get("layer", "base")!r})')
    if op == "overlay":
        color = f', color={_crepr(p["color"])}' if p.get("color") else ""
        return (f'apply_overlay(s, {p["part"]!r}, {p["overlay"]!r}'
                f'{color}, layer={p.get("layer", "base")!r}, seed={p.get("seed", 0)!r})')
    if op == "decorate":
        args = []
        for k in ("hat", "jacket", "pants"):
            if p.get(k):
                args.append(f"{k}_color={_crepr(p[k])}")
        return "apply_3d_decoration(s, " + ", ".join(args) + ")"
    if op == "face":
        args = []
        for k in ("eyes", "brows", "mouth"):
            if p.get(k):
                args.append(f"{k}_color={_crepr(p[k])}")
        return "face(s, " + ", ".join(args) + ")"
    if op == "hair":
        args = [f"{_crepr(p['color'])}"]
        for k in ("light", "dark"):
            if p.get(k):
                args.append(f"{k}={_crepr(p[k])}")
        return "hair(s, " + ", ".join(args) + ")"
    if op == "band":
        return (f'band(s, {p["part"]!r}, {p["v0"]!r}, {p["v1"]!r}, {_crepr(p["color"])}, '
                f'layer={p.get("layer", "overlay")!r})')
    if op == "outline":
        return (f'outline(s, {p["part"]!r}, {_crepr(p["color"])}, '
                f'layer={p.get("layer", "base")!r}, width={p.get("width", 1)!r})')
    if op == "pixel":
        return (f's.pixel({p["part"]!r}, {p.get("layer", "base")!r}, {p["face"]!r}, '
                f'{p["u"]!r}, {p["v"]!r}, {_crepr(p["color"])})')
    if op == "paint":
        if p.get("face"):
            return (f's.paint_face({p["part"]!r}, {p.get("layer", "base")!r}, '
                    f'{p["face"]!r}, {_crepr(p["color"])})')
        return (f's.paint_part({p["part"]!r}, {_crepr(p["color"])}, '
                f'{p.get("layer", "base")!r})')
    raise ValueError(f"unknown op {op!r}")


def recipe_to_python(recipe) -> str:
    """Return an equivalent standalone Python script for a recipe."""
    if isinstance(recipe, (str, Path)):
        text = recipe if not Path(recipe).exists() else Path(recipe).read_text(encoding="utf-8")
        recipe = json.loads(text)

    lines = [
        "from skinlib import (Skin, apply_shading, apply_material, apply_overlay,",
        "    apply_3d_decoration, face, hair, band, outline)",
        "",
    ]
    if recipe.get("base"):
        lines.append("from skinlib import build_template")
        lines.append(f"s = build_template({recipe['base']!r})")
    else:
        lines.append(f"s = Skin(size={recipe.get('size', 64)!r}, "
                     f"model={recipe.get('model', 'steve')!r})")
    for step in recipe.get("steps", []):
        lines.append(_emit(step))
    if recipe.get("output"):
        lines.append(f's.save({recipe["output"]!r})')
    return "\n".join(lines) + "\n"
