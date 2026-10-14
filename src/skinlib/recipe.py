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

A recipe whose **first step is ``texture``** builds a texture (a block sheet or
an item icon) instead of a skin, and may then use the canvas-generic ops
(``shading``/``material``/``pattern``/``overlay``/``outline``/``pixel``/
``paint``); the skin-only ops (``face``/``hair``/``band``/``decorate``) refuse
it::

    {
      "steps": [
        {"op": "texture", "name": "sculk_sensor", "color": "#2a4d4a",
         "noise": 4, "seed": 1},
        {"op": "overlay", "part": "all", "overlay": "runes",
         "color": "#7fffd4", "seed": 3}
      ],
      "output_dir": "out/sculk"   # one PNG per face, named sculk_sensor_*.png
    }

Colors may be written as ``"R,G,B"`` / ``"R,G,B,A"`` / ``"#RRGGBB"`` strings or
as ``[r, g, b]`` / ``[r, g, b, a]`` lists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Union

from .colors import parse_color
from .skin import Skin
from .shading import apply_shading, outline
from .patterns import apply_pattern
from .materials import apply_material
from .overlay import apply_overlay
from .decoration import apply_3d_decoration
from .features import face, hair, band
from .templates import build_template
from .texture import BLOCK_FACES, Texture, block, generate, icon


def _col(v: Any) -> tuple:
    if isinstance(v, str):
        return parse_color(v)
    c = tuple(v)
    if len(c) == 3:            # the documented [r, g, b] form
        return (*c, 255)
    if len(c) == 4:
        return c
    raise ValueError(f"expected RGB or RGBA, got {c!r}")


def _maybe_col(v: Any):
    return _col(v) if v is not None else None


def _require_skin(canvas: Any, op: str) -> None:
    """Skin-only ops have to fail loudly on a texture canvas.

    Their part/face coordinates would otherwise silently paint unrelated pixels
    of a block sheet instead of raising.
    """
    if not isinstance(canvas, Skin):
        raise ValueError(
            f"op {op!r} needs a skin canvas, but this recipe is painting a "
            f"{type(canvas).__name__}; texture recipes can use shading, "
            f"material, pattern, overlay, outline, pixel and paint")


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
    _require_skin(s, "decorate")
    apply_3d_decoration(
        s,
        hat_color=_maybe_col(p.get("hat")),
        jacket_color=_maybe_col(p.get("jacket")),
        pants_color=_maybe_col(p.get("pants")),
    )
    return s


def _op_face(s: Skin, p: dict) -> Skin:
    _require_skin(s, "face")
    face(s,
         eye_color=_maybe_col(p.get("eyes")) or (96, 226, 140, 255),
         brow_color=_maybe_col(p.get("brows")) or (120, 110, 105, 255),
         mouth_color=_maybe_col(p.get("mouth")) or (110, 92, 88, 255))
    return s


def _op_hair(s: Skin, p: dict) -> Skin:
    _require_skin(s, "hair")
    hair(s, _col(p["color"]),
         light=_maybe_col(p.get("light")),
         dark=_maybe_col(p.get("dark")))
    return s


def _op_band(s: Skin, p: dict) -> Skin:
    _require_skin(s, "band")
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


# ---------------------------------------------------------------------------
# Texture op: the canvas source of a texture recipe
# ---------------------------------------------------------------------------
# Keys forwarded to skinlib.texture's generators.  ``mask`` is deliberately
# absent: a per-pixel silhouette is not listable in JSON.
_TEXTURE_KEYS = ("style", "material", "noise", "seed", "glow", "glow_strength",
                 "tint_ready", "alpha", "size")


def _texture_kwargs(p: dict) -> dict:
    return {k: p[k] for k in _TEXTURE_KEYS if k in p}


def _op_texture(canvas: Any, p: dict) -> Texture:
    """Build the canvas of a texture recipe: a block sheet or an item icon.

    With ``name`` the texture comes from the gamedata registry (version/edition
    select the pack, as in ``mc-skin texture``); without it, ``kind: "item"``
    makes an icon (``shape``, default ``gem``) and anything else a block sheet
    (``faces``, default the six cube faces).
    """
    color = _col(p["color"])
    if p.get("name"):
        kw = _texture_kwargs(p)
        for k in ("version", "edition", "shape"):
            if k in p:
                kw[k] = p[k]
        return generate(p["name"], color, **kw)
    if p.get("kind") == "item":
        return icon(color, shape=p.get("shape", "gem"), **_texture_kwargs(p))
    return block(color, faces=tuple(p.get("faces", BLOCK_FACES)),
                 **_texture_kwargs(p))


OPS: Dict[str, Callable[[Any, dict], Any]] = {
    "texture": _op_texture,
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
def generate_from_recipe(recipe, output: str = None) -> Union[Skin, Texture]:
    """Build a skin or a texture from a recipe.

    Accepts a dict, a JSON string, or a path to a JSON file.  A recipe whose
    first step is ``texture`` builds a :class:`~skinlib.texture.Texture` (block
    sheet or item icon) and may then use the canvas-generic ops.  Returns the
    canvas, saved when the recipe asks for it: ``output`` for a single file,
    ``output_dir`` for one PNG per face.
    """
    if isinstance(recipe, (str, Path)):
        text = recipe if not Path(recipe).exists() else Path(recipe).read_text(encoding="utf-8")
        recipe = json.loads(text)

    steps = list(recipe.get("steps", []))
    source = steps[0] if steps and steps[0].get("op") == "texture" else None
    canvas: Union[Skin, Texture]
    if source is not None:
        canvas = _op_texture(None, source)
        steps = steps[1:]
    elif recipe.get("base"):
        canvas = build_template(recipe["base"])
    else:
        canvas = Skin(size=recipe.get("size", 64),
                      model=recipe.get("model", "steve"))

    for step in steps:
        op = step.get("op")
        if op == "texture":
            raise ValueError("the 'texture' op must be the first step: it "
                             "replaces the canvas")
        if op not in OPS:
            raise ValueError(f"unknown op {op!r}; choices: {sorted(OPS)}")
        canvas = OPS[op](canvas, step)

    out = output or recipe.get("output")
    if out:
        canvas.save(out)
    outdir = recipe.get("output_dir")
    if outdir:
        if not isinstance(canvas, Texture):
            raise ValueError("output_dir writes one PNG per face, so it needs a "
                             "texture recipe; a skin saves to a single 'output'")
        canvas.save_faces(outdir, recipe.get("prefix")
                          or (source or {}).get("name") or "texture")
    return canvas


# ---------------------------------------------------------------------------
# Codegen (emit an imperative Python script from a recipe)
# ---------------------------------------------------------------------------
def _crepr(v: Any) -> str:
    return repr(tuple(_col(v)))


def _emit_shading(p: dict) -> str:
    return (f'apply_shading(s, {p["part"]!r}, {_crepr(p["color"])}, '
            f'{p.get("layer", "base")!r}, style={p.get("style", "combined")!r}, '
            f'noise={p.get("noise", False)!r}, seed={p.get("seed", 0)!r})')


def _emit_material(p: dict) -> str:
    color = f', color={_crepr(p["color"])}' if p.get("color") else ""
    return (f'apply_material(s, {p["part"]!r}, {p["material"]!r}'
            f'{color}, layer={p.get("layer", "base")!r})')


def _emit_pattern(p: dict) -> str:
    name = p["pattern"]
    layer = p.get("layer", "base")
    if name == "camouflage":
        palette = ", ".join(_crepr(c) for c in p.get("palette", []))
        return (f'apply_pattern(s, "camouflage", [{palette}], part={p["part"]!r}, '
                f'layer={layer!r}, seed={p.get("seed", 0)!r})')
    if name == "stripes":
        return (f'apply_pattern(s, "stripes", {p["part"]!r}, {_crepr(p["c1"])}, '
                f'{_crepr(p["c2"])}, layer={layer!r}, '
                f'direction={p.get("direction", "vertical")!r}, '
                f'width={p.get("width", 2)!r})')
    if name == "checker":
        return (f'apply_pattern(s, "checker", {p["part"]!r}, {_crepr(p["c1"])}, '
                f'{_crepr(p["c2"])}, layer={layer!r}, cell={p.get("cell", 4)!r})')
    if name == "border_trim":
        return (f'apply_pattern(s, "border_trim", {p["part"]!r}, {_crepr(p["c1"])}, '
                f'{_crepr(p["c2"])}, layer={layer!r}, width={p.get("width", 1)!r})')
    raise ValueError(f"unknown pattern {name!r}")


def _emit_overlay(p: dict) -> str:
    color = f', color={_crepr(p["color"])}' if p.get("color") else ""
    return (f'apply_overlay(s, {p["part"]!r}, {p["overlay"]!r}'
            f'{color}, layer={p.get("layer", "base")!r}, seed={p.get("seed", 0)!r})')


def _emit_decorate(p: dict) -> str:
    args = []
    for k in ("hat", "jacket", "pants"):
        if p.get(k):
            args.append(f"{k}_color={_crepr(p[k])}")
    return "apply_3d_decoration(s, " + ", ".join(args) + ")"


def _emit_face(p: dict) -> str:
    # Recipe keys map to face() parameter names (eyes -> eye_color, brows -> brow_color).
    args = []
    for k, param in (("eyes", "eye_color"), ("brows", "brow_color"), ("mouth", "mouth_color")):
        if p.get(k):
            args.append(f"{param}={_crepr(p[k])}")
    return "face(s, " + ", ".join(args) + ")"


def _emit_hair(p: dict) -> str:
    args = [f"{_crepr(p['color'])}"]
    for k in ("light", "dark"):
        if p.get(k):
            args.append(f"{k}={_crepr(p[k])}")
    return "hair(s, " + ", ".join(args) + ")"


def _emit_band(p: dict) -> str:
    return (f'band(s, {p["part"]!r}, {p["v0"]!r}, {p["v1"]!r}, {_crepr(p["color"])}, '
            f'layer={p.get("layer", "overlay")!r})')


def _emit_outline(p: dict) -> str:
    return (f'outline(s, {p["part"]!r}, {_crepr(p["color"])}, '
            f'layer={p.get("layer", "base")!r}, width={p.get("width", 1)!r})')


def _emit_pixel(p: dict) -> str:
    return (f's.pixel({p["part"]!r}, {p.get("layer", "base")!r}, {p["face"]!r}, '
            f'{p["u"]!r}, {p["v"]!r}, {_crepr(p["color"])})')


def _emit_paint(p: dict) -> str:
    if p.get("face"):
        return (f's.paint_face({p["part"]!r}, {p.get("layer", "base")!r}, '
                f'{p["face"]!r}, {_crepr(p["color"])})')
    return (f's.paint_part({p["part"]!r}, {_crepr(p["color"])}, '
            f'{p.get("layer", "base")!r})')


def _emit_texture(p: dict) -> str:
    color = _crepr(p["color"])
    kw = [f"{k}={p[k]!r}" for k in _TEXTURE_KEYS if k in p]
    if p.get("name"):
        kw += [f"{k}={p[k]!r}" for k in ("version", "edition", "shape") if k in p]
        return ", ".join([f"generate({p['name']!r}", color] + kw) + ")"
    if p.get("kind") == "item":
        kw.insert(0, f"shape={p.get('shape', 'gem')!r}")
        return ", ".join([f"icon({color}"] + kw) + ")"
    if "faces" in p:
        kw.insert(0, f"faces={tuple(p['faces'])!r}")
    return ", ".join([f"block({color}"] + kw) + ")"


_EMITTERS: Dict[str, Callable[[dict], str]] = {
    "texture": _emit_texture,
    "shading": _emit_shading,
    "material": _emit_material,
    "pattern": _emit_pattern,
    "overlay": _emit_overlay,
    "decorate": _emit_decorate,
    "face": _emit_face,
    "hair": _emit_hair,
    "band": _emit_band,
    "outline": _emit_outline,
    "pixel": _emit_pixel,
    "paint": _emit_paint,
}


def _emit(step: dict) -> str:
    op = step["op"]
    emitter = _EMITTERS.get(op)
    if emitter is None:
        raise ValueError(f"unknown op {op!r}; choices: {sorted(_EMITTERS)}")
    return emitter(step)


def recipe_to_python(recipe) -> str:
    """Return an equivalent standalone Python script for a recipe."""
    if isinstance(recipe, (str, Path)):
        text = recipe if not Path(recipe).exists() else Path(recipe).read_text(encoding="utf-8")
        recipe = json.loads(text)

    steps = list(recipe.get("steps", []))
    source = steps[0] if steps and steps[0].get("op") == "texture" else None
    if source is not None:
        steps = steps[1:]

    lines = []
    if source is not None:
        lines.append("from skinlib import (block, generate, icon, apply_shading,")
        lines.append("    apply_material, apply_overlay, apply_pattern, outline)")
    else:
        lines.append("from skinlib import (Skin, apply_shading, apply_material, apply_overlay,")
        lines.append("    apply_3d_decoration, apply_pattern, face, hair, band, outline)")
    lines.append("")
    if source is not None:
        lines.append(f"s = {_emit_texture(source)}")
    elif recipe.get("base"):
        lines.append("from skinlib import build_template")
        lines.append(f"s = build_template({recipe['base']!r})")
    else:
        lines.append(f"s = Skin(size={recipe.get('size', 64)!r}, "
                     f"model={recipe.get('model', 'steve')!r})")
    for step in steps:
        if step.get("op") == "texture":
            raise ValueError("the 'texture' op must be the first step: it "
                             "replaces the canvas")
        lines.append(_emit(step))
    if recipe.get("output"):
        lines.append(f's.save({recipe["output"]!r})')
    if recipe.get("output_dir"):
        prefix = (recipe.get("prefix")
                  or (source.get("name") if source else None) or "texture")
        lines.append(f's.save_faces({recipe["output_dir"]!r}, {prefix!r})')
    return "\n".join(lines) + "\n"
