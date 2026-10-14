#!/usr/bin/env python3
"""Unified CLI for the Minecraft skin library.

Usage:
    python skin_tool.py create -o skin.png --size 64 --model steve
    python skin_tool.py paint skin.png --part head --layer base --color 240,190,150
    python skin_tool.py shading skin.png --part body --color 120,20,25 --style combined --noise
    python skin_tool.py pattern skin.png --part body --pattern stripes --c1 200,0,0 --c2 255,255,255
    python skin_tool.py template knight -o knight.png
    python skin_tool.py decorate skin.png --hat 200,30,30 --jacket 30,30,40 --pants 20,40,90
    python skin_tool.py sample ref.png --colors 6
    python skin_tool.py harmonize skin.png --reference cape.png
    python skin_tool.py render skin.png --outdir previews
    python skin_tool.py info skin.png
    python skin_tool.py flatten skin.png
    python skin_tool.py open skin.png
    python skin_tool.py gamedata styles --version 1.21.6
    python skin_tool.py gamedata style sculk
    python skin_tool.py gamedata formats
    python skin_tool.py gamedata spec sculk_sensor
    python skin_tool.py texture sculk_sensor --color 42,77,74 --scale 8
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .colors import parse_color
from .model import PARTS, LAYERS, FACES
from .skin import Skin, create, load
from .shading import apply_shading, outline, STYLE_PROFILES, SHADING_STYLES
from .patterns import apply_pattern, PATTERNS
from .sampling import sample_palette
from .render import save_previews, render_3d
from .templates import build_template, TEMPLATES
from .palette import all_palettes
from .validate import validate_report
from .poses import POSES
from .decoration import apply_3d_decoration
from .features import face, hair, band
from .materials import apply_material, MATERIALS
from .overlay import apply_overlay, OVERLAYS
from .recipe import generate_from_recipe
from .harmonize import MODES as HARMONIZE_MODES, harmonize_report, region_mask
from .transforms import detect_model
from . import texture as T
from . import gamedata as G

DEFAULT_BLOCKBENCH = os.environ.get("BLOCKBENCH", r"C:\Program Files\Blockbench\Blockbench.exe")


def _cmd_create(a):
    create(size=a.size, model=a.model).save(a.output)
    print(f"created {a.output} ({a.size}x{a.size}, {a.model})")


def _cmd_paint(a):
    s = load(a.input, model=a.model)
    c = parse_color(a.color)
    out = a.output or a.input
    if a.face:
        s.paint_face(a.part, a.layer, a.face, c)
    else:
        s.paint_part(a.part, c, a.layer)
    s.save(out)
    print(f"painted {a.part}/{a.layer} -> {out}")


def _cmd_shading(a):
    s = load(a.input, model=a.model)
    c = parse_color(a.color)
    out = a.output or a.input
    apply_shading(s, a.part, c, layer=a.layer, style=a.style,
                  noise=a.noise, noise_var=a.noise_var, seed=a.seed)
    s.save(out)
    print(f"shaded {a.part}/{a.layer} ({a.style}) -> {out}")


def _cmd_material(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    apply_material(s, a.part, a.material,
                   color=parse_color(a.color) if a.color else None,
                   layer=a.layer, seed=a.seed)
    s.save(out)
    print(f"material {a.material} -> {out}")


def _cmd_overlay(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    kw = {}
    if a.color:
        kw["color"] = parse_color(a.color)
    if a.count is not None:
        kw["count"] = a.count
    apply_overlay(s, a.part, a.overlay, layer=a.layer, seed=a.seed, **kw)
    s.save(out)
    print(f"overlay {a.overlay} -> {out}")


def _cmd_recipe(a):
    generate_from_recipe(a.recipe, output=a.output)
    print("recipe done")


def _cmd_pattern(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    c1 = parse_color(a.c1) if a.c1 else None
    c2 = parse_color(a.c2) if a.c2 else None
    if a.pattern == "stripes":
        apply_pattern(s, "stripes", a.part, c1, c2, layer=a.layer,
                      direction=a.direction, width=a.width)
    elif a.pattern == "checker":
        apply_pattern(s, "checker", a.part, c1, c2, layer=a.layer, cell=a.cell)
    elif a.pattern == "camouflage":
        pal = [parse_color(x) for x in a.palette.split()] if a.palette \
            else [(60, 80, 40, 255), (100, 120, 60, 255), (40, 60, 30, 255)]
        apply_pattern(s, "camouflage", pal, part=a.part, layer=a.layer, seed=a.seed)
    elif a.pattern == "border_trim":
        apply_pattern(s, "border_trim", a.part, c1 or (0,0,0,255),
                      c2 or (255,255,255,255), layer=a.layer, width=a.width)
    s.save(out)
    print(f"pattern {a.pattern} -> {out}")


def _cmd_template(a):
    build_template(a.name).save(a.output)
    print(f"template {a.name} -> {a.output}")


def _cmd_decorate(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    apply_3d_decoration(
        s,
        hat_color=parse_color(a.hat) if a.hat else None,
        jacket_color=parse_color(a.jacket) if a.jacket else None,
        pants_color=parse_color(a.pants) if a.pants else None,
    )
    s.save(out)
    print(f"decorated -> {out}")


def _cmd_hair(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    hair(s, parse_color(a.color),
         light=parse_color(a.light) if a.light else None,
         dark=parse_color(a.dark) if a.dark else None)
    s.save(out)
    print(f"hair -> {out}")


def _cmd_face(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    face(s,
         eye_color=parse_color(a.eyes) if a.eyes else (96, 226, 140, 255),
         brow_color=parse_color(a.brows) if a.brows else (120, 110, 105, 255),
         mouth_color=parse_color(a.mouth) if a.mouth else (110, 92, 88, 255))
    s.save(out)
    print(f"face -> {out}")


def _cmd_band(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    band(s, a.part, a.v0, a.v1, parse_color(a.color), layer=a.layer)
    s.save(out)
    print(f"band -> {out}")


def _cmd_outline(a):
    s = load(a.input, model=a.model)
    out = a.output or a.input
    outline(s, a.part, parse_color(a.color), layer=a.layer, width=a.width)
    s.save(out)
    print(f"outlined {a.part}/{a.layer} -> {out}")


def _cmd_open(a):
    exe = a.blockbench or DEFAULT_BLOCKBENCH
    subprocess.Popen([exe, a.input])
    print(f"opened {a.input} in Blockbench")


def _cmd_sample(a):
    colors = sample_palette(a.input, a.colors)
    print(f"palette from {a.input}:")
    for i, c in enumerate(colors):
        print(f"  {i}: #{c[0]:02x}{c[1]:02x}{c[2]:02x}  RGB{c[:3]}")


def _cmd_render(a):
    s = load(a.input, model=a.model)
    save_previews(s, a.outdir, scale=a.scale)
    print(f"previews -> {a.outdir}/ (flat.png, iso_front/back.png, render_3d.png)")


def _cmd_info(a):
    s = load(a.input, model=a.model)
    print(f"file:   {a.input}")
    print(f"size:   {s.size}x{s.size}")
    print(f"model:  {s.model}")
    for layer in LAYERS:
        img = s.layer_image(layer)
        a_ch = img.getchannel("A")
        n = sum(1 for v in a_ch.tobytes() if v > 0)
        print(f"  {layer}: {n} opaque px")
    from collections import Counter
    c = Counter()
    for cnt, col in s.img.getcolors(maxcolors=1_000_000):
        if col[3] > 0:
            c[col[:3]] = cnt
    print(f"  distinct colors: {len(c)}")


def _cmd_flatten(a):
    s = load(a.input, model=a.model)
    out = a.output or Path(a.input).stem + "_flat.png"
    s.flatten().save(str(out))
    print(f"flattened -> {out}")


def _cmd_pose(a):
    s = load(a.input, model=a.model)
    out = a.output or Path(a.input).stem + f"_{a.pose}.png"
    render_3d(s, yaw=a.yaw, pitch=a.pitch, pose=a.pose, scale=a.scale).save(out)
    print(f"rendered pose '{a.pose}' -> {out}")


def _cmd_validate(a):
    print(validate_report(a.input))


def _cmd_palette(a):
    palettes = all_palettes()
    if a.category:
        cat = palettes.get(a.category)
        if not cat:
            sys.exit(f"unknown category; choices: {sorted(palettes)}")
        print(f"{a.category}:")
        for name, c in cat.items():
            print(f"  {name:15s} #{c[0]:02x}{c[1]:02x}{c[2]:02x}")
    else:
        for cat, colors in palettes.items():
            print(f"[{cat}] {len(colors)} colors")
            for name, c in colors.items():
                print(f"  {name:15s} #{c[0]:02x}{c[1]:02x}{c[2]:02x}")


def _cmd_harmonize(a):
    """Recolor a texture into another's color family (e.g. a skin onto a cape)."""
    from PIL import Image

    def split(value):
        return tuple(v.strip() for v in value.split(",") if v.strip()) if value else None

    parts, layers, faces = split(a.parts), split(a.layers), split(a.faces)
    mask = None
    if parts or layers or faces:
        img = Image.open(a.input)
        if img.width != img.height or img.width not in (64, 128):
            raise SystemExit("--parts/--layers/--faces need a 64x64 or 128x128 skin")
        model = a.model if a.model != "auto" else detect_model(img.convert("RGBA"))
        mask = region_mask(model, img.width, parts, layers, faces)

    report = harmonize_report(a.input, a.reference, mode=a.mode,
                              strength=a.strength, mask=mask)
    out = a.output or str(Path(a.input).with_name(Path(a.input).stem + "_matched.png"))
    report["image"].save(out)
    where = "whole texture" if mask is None else ", ".join(
        filter(None, [f"parts={'+'.join(parts)}" if parts else "",
                      f"layers={'+'.join(layers)}" if layers else "",
                      f"faces={'+'.join(faces)}" if faces else ""]))
    print(f"harmonized {a.input} -> {out}")
    print(f"  mode={a.mode} strength={a.strength} ({where})")
    print(f"  color difference vs {a.reference}: "
          f"dE {report['delta_before']:.1f} -> {report['delta_after']:.1f}")


def _cmd_gamedata(a):
    """Inspect the vanilla data layer (see :mod:`skinlib.gamedata`)."""
    if not G.available():
        raise SystemExit(G.INSTALL_HINT)
    ed = a.edition
    if a.what == "overview":
        ov = G.overview(a.version, ed)
        print(f"{ov['edition']} {ov['version']}  --  {ov['versions']} versions available")
        print(f"data: {ov['source']}")
        for name, count in ov["datasets"].items():
            print(f"  {name:22} {count}")
    elif a.what == "versions":
        vs = G.versions(ed)
        print(f"{len(vs)} loadable versions for {ed}; latest = {G.latest(ed)}")
        print("  " + ", ".join(vs[-a.limit:]))
    elif a.what == "styles":
        found = G.styles(a.version, ed, min_members=a.min_members)
        if a.term:
            found = {k: v for k, v in found.items() if a.term in k}
        print(f"{len(found)} style families with >= {a.min_members} members")
        for name, s in list(found.items())[:a.limit]:
            notes = []
            if s.glow:
                notes.append(f"glow={len(s.glow)}")
            if s.entities:
                notes.append(f"entities={len(s.entities)}")
            if s.tint_group:
                notes.append(f"tints={len(s.tint_colors)}")
            head = ", ".join(s.names[:6]) + (" ..." if len(s.names) > 6 else "")
            print(f"  {name:14} blocks={len(s.blocks):4} items={len(s.items):4} "
                  f"{' '.join(notes)}")
            print(f"      {head}")
    elif a.what == "style":
        if not a.term:
            raise SystemExit("usage: gamedata style <name>")
        s = G.style(a.term, a.version, ed)
        print(f"{s.name}  ({s.edition} {s.version}, {len(s)} members)")
        print(f"  blocks    : {', '.join(s.block_names) or '-'}")
        print(f"  items     : {', '.join(s.item_names) or '-'}")
        if s.entities:
            print(f"  entities  : {', '.join(e.name for e in s.entities)}")
        if s.particles:
            print(f"  particles : {', '.join(p.name for p in s.particles)}")
        if s.glow:
            print(f"  glow      : {', '.join(s.glow)}")
        print(f"  materials : {', '.join(s.materials)}   transparent={s.transparent}")
        for entry in s.tint_colors[:6]:
            print(f"  tint {entry.hex} over {len(entry.biomes)} biomes")
    elif a.what == "search":
        if not a.term:
            raise SystemExit("usage: gamedata search <phrase>")
        hits = G.search(a.term, a.version, ed, limit=a.limit)
        print(f"{len(hits)} hits for {a.term!r}")
        for hit in hits:
            print(f"  {hit.kind:9} {hit.name:34} {hit.display_name}")
    elif a.what == "formats":
        for name, fmt in G.skin_formats().items():
            print(f"[{name}] {fmt.schema}")
            print(f"  image={fmt.image} arm={fmt.arm_size!r} cape={fmt.cape_image} "
                  f"geometry={fmt.geometry_format!r} persona={fmt.persona} "
                  f"animated={fmt.animated_frames}")
            print(f"  fields: {', '.join(fmt.fields)}")
    elif a.what in ("blocks", "items", "entities", "particles"):
        rows = getattr(G, a.what)(a.version, ed)
        if a.term:
            rows = [r for r in rows if a.term in r.name]
        print(f"{len(rows)} {a.what} in {ed} {G.resolve(a.version, ed)}")
        for row in rows[:a.limit]:
            display = getattr(row, "display_name", row.name)
            light = f"  light={row.emit_light}" if getattr(row, "glows", False) else ""
            print(f"  {row.name:38} {display}{light}")
    elif a.what == "biomes":
        rows = G.biomes(a.version, ed)
        print(f"{len(rows)} biomes in {ed} {G.resolve(a.version, ed)}")
        print("  (grass_tint is the verified vanilla tint; the record's own `color`")
        print("   field is raw data and does not match the vanilla biome colors)")
        for b in rows[:a.limit]:
            tint = G.tint_color("grass", b.name, a.version, ed)
            shown = "#%06x" % tint if tint else "-"
            print(f"  {b.name:26} {b.dimension:10} {b.category:12} "
                  f"temp={b.temperature:<5} grass_tint={shown}")
    elif a.what == "tints":
        for group, entries in G.tints(a.version, ed).items():
            print(f"{group}: {len(entries)} entries")
            for entry in entries[:a.limit]:
                print(f"  {entry.hex}  {len(entry.biomes)} biomes")
    elif a.what == "palette":
        group = a.term or "grass"
        pal = G.biome_colors(group, a.version, ed)
        print(f"{len(pal)} biomes tinted by {group!r}")
        for name, hexv in list(pal.items())[:a.limit]:
            print(f"  {name:26} {hexv}")
    elif a.what == "spec":
        if not a.term:
            raise SystemExit("usage: gamedata spec <block-or-item>")
        s = G.texture_spec(a.term, a.version, ed)
        print(f"{s.kind}: {s.name}  ({s.display_name})")
        print(f"  size={s.size}  emissive={s.emissive}  "
              f"transparent={s.transparent}")
        print(f"  tint={s.tint_group or '-'}  material={s.material or '-'}  "
              f"style={s.style or '-'}")
        if s.family:
            print(f"  family ({len(s.family)}): {', '.join(s.family)}")
        for state, values in s.states:
            print(f"  state {state}: "
                  f"{', '.join(values) if values else '(bool)'}")

    elif a.what == "theme":
        if not a.term:
            raise SystemExit(
                "usage: gamedata theme <name>, e.g. `gamedata theme sculk`")
        grouped = G.theme(a.term, a.version, ed)
        total = sum(len(v) for v in grouped.values())
        print(f"{a.term} theme: {total} entries "
              f"({ed} {G.resolve(a.version, ed)})")
        for kind, entries in grouped.items():
            print(f"  {kind} ({len(entries)})")
            for entry in entries[:a.limit]:
                props = " ".join(f"{k}={v}" for k, v in entry.properties.items()
                                 if v not in ("", 0.0, 0, False, None))
                print(f"    {entry.name:34} {entry.display_name:26} {props}")


def _cmd_texture(a):
    """Generate a texture that is not a skin: a block sheet or an item icon."""
    if not G.available():
        raise SystemExit(G.INSTALL_HINT)
    spec = G.texture_spec(a.name, a.version, a.edition)
    tex = T.from_spec(spec, parse_color(a.color), style=a.style,
                      material=a.material, shape=a.shape, noise=a.noise,
                      seed=a.seed, glow=a.glow, glow_strength=a.glow_strength,
                      tint_ready=a.tint_ready, alpha=a.alpha)
    print(f"{spec.kind}: {spec.name}  ({spec.display_name})")
    print(f"  sheet {tex.width}x{tex.height}, faces: {', '.join(tex.faces)}")
    print(f"  emissive={spec.emissive}  transparent={spec.transparent}  "
          f"tint={spec.tint_group or '-'}  material={spec.material or '-'}  "
          f"style={spec.style or '-'}")
    for state, values in spec.states:
        shown = ", ".join(values[:8]) + (" ..." if len(values) > 8 else "")
        print(f"  variant state {state}: {shown or '(bool)'}")
    for path in tex.save_faces(a.outdir, spec.name, scale=a.scale):
        print(f"  -> {path}")


def build_parser():
    p = argparse.ArgumentParser(description="Minecraft skin library")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create"); c.add_argument("-o", "--output", default="skin.png")
    c.add_argument("--size", type=int, choices=(64, 128), default=64)
    c.add_argument("--model", choices=("steve", "alex"), default="steve")
    c.set_defaults(func=_cmd_create)

    pa = sub.add_parser("paint"); pa.add_argument("input")
    pa.add_argument("--part", required=True, choices=PARTS)
    pa.add_argument("--layer", required=True, choices=LAYERS)
    pa.add_argument("--color", required=True)
    pa.add_argument("--face", choices=FACES, default=None)
    pa.add_argument("-o", "--output", default=None)
    pa.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    pa.set_defaults(func=_cmd_paint)

    sh = sub.add_parser("shading"); sh.add_argument("input")
    sh.add_argument("--part", required=True, choices=PARTS)
    sh.add_argument("--color", required=True)
    sh.add_argument("--layer", choices=LAYERS, default="base")
    sh.add_argument("--style", choices=("flat", "vertical", "cylindrical", "combined", "artistic"), default="combined")
    sh.add_argument("--noise", action="store_true")
    sh.add_argument("--noise-var", type=int, default=6)
    sh.add_argument("--seed", type=int, default=0)
    sh.add_argument("-o", "--output", default=None)
    sh.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    sh.set_defaults(func=_cmd_shading)

    m = sub.add_parser("material"); m.add_argument("input")
    m.add_argument("--part", required=True, choices=PARTS)
    m.add_argument("--material", required=True, choices=sorted(MATERIALS))
    m.add_argument("--color", default=None, help="base color (R,G,B)")
    m.add_argument("--layer", choices=LAYERS, default="base")
    m.add_argument("--seed", type=int, default=None)
    m.add_argument("-o", "--output", default=None)
    m.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    m.set_defaults(func=_cmd_material)

    ov = sub.add_parser("overlay"); ov.add_argument("input")
    ov.add_argument("--part", required=True, choices=PARTS)
    ov.add_argument("--overlay", required=True, choices=sorted(OVERLAYS))
    ov.add_argument("--color", default=None, help="effect color (R,G,B)")
    ov.add_argument("--layer", choices=LAYERS, default="base")
    ov.add_argument("--count", type=int, default=None)
    ov.add_argument("--seed", type=int, default=0)
    ov.add_argument("-o", "--output", default=None)
    ov.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    ov.set_defaults(func=_cmd_overlay)

    rc = sub.add_parser("recipe"); rc.add_argument("recipe", help="recipe JSON file or inline JSON")
    rc.add_argument("-o", "--output", default=None)
    rc.set_defaults(func=_cmd_recipe)

    pt = sub.add_parser("pattern"); pt.add_argument("input")
    pt.add_argument("--part", required=True, choices=PARTS)
    pt.add_argument("--pattern", required=True, choices=sorted(PATTERNS))
    pt.add_argument("--layer", choices=LAYERS, default="base")
    pt.add_argument("--c1", default=None); pt.add_argument("--c2", default=None)
    pt.add_argument("--palette", default=None)
    pt.add_argument("--direction", choices=("vertical", "horizontal"), default="vertical")
    pt.add_argument("--width", type=int, default=2)
    pt.add_argument("--cell", type=int, default=4)
    pt.add_argument("--seed", type=int, default=0)
    pt.add_argument("-o", "--output", default=None)
    pt.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    pt.set_defaults(func=_cmd_pattern)

    t = sub.add_parser("template"); t.add_argument("name", choices=sorted(TEMPLATES))
    t.add_argument("-o", "--output", default="skin.png")
    t.set_defaults(func=_cmd_template)

    dec = sub.add_parser("decorate"); dec.add_argument("input")
    dec.add_argument("--hat", default=None, help="hat color (R,G,B)")
    dec.add_argument("--jacket", default=None, help="jacket/zipper color (R,G,B)")
    dec.add_argument("--pants", default=None, help="pants hem color (R,G,B)")
    dec.add_argument("-o", "--output", default=None)
    dec.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    dec.set_defaults(func=_cmd_decorate)

    h = sub.add_parser("hair"); h.add_argument("input")
    h.add_argument("--color", required=True, help="hair color (R,G,B)")
    h.add_argument("--light", default=None, help="strand highlight (R,G,B)")
    h.add_argument("--dark", default=None, help="strand shadow (R,G,B)")
    h.add_argument("-o", "--output", default=None)
    h.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    h.set_defaults(func=_cmd_hair)

    fa = sub.add_parser("face"); fa.add_argument("input")
    fa.add_argument("--eyes", default=None, help="eye color (R,G,B)")
    fa.add_argument("--brows", default=None, help="brow color (R,G,B)")
    fa.add_argument("--mouth", default=None, help="mouth color (R,G,B)")
    fa.add_argument("-o", "--output", default=None)
    fa.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    fa.set_defaults(func=_cmd_face)

    b = sub.add_parser("band"); b.add_argument("input")
    b.add_argument("--part", required=True, choices=PARTS)
    b.add_argument("--v0", type=int, required=True, help="first row (inclusive)")
    b.add_argument("--v1", type=int, required=True, help="last row (inclusive)")
    b.add_argument("--color", required=True)
    b.add_argument("--layer", choices=LAYERS, default="overlay")
    b.add_argument("-o", "--output", default=None)
    b.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    b.set_defaults(func=_cmd_band)

    ol = sub.add_parser("outline"); ol.add_argument("input")
    ol.add_argument("--part", required=True, choices=PARTS)
    ol.add_argument("--color", required=True)
    ol.add_argument("--layer", choices=LAYERS, default="base")
    ol.add_argument("--width", type=int, default=1)
    ol.add_argument("-o", "--output", default=None)
    ol.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    ol.set_defaults(func=_cmd_outline)

    op = sub.add_parser("open"); op.add_argument("input")
    op.add_argument("--blockbench", default=None, help="Blockbench.exe path")
    op.set_defaults(func=_cmd_open)

    sm = sub.add_parser("sample"); sm.add_argument("input")
    sm.add_argument("--colors", type=int, default=6)
    sm.set_defaults(func=_cmd_sample)

    r = sub.add_parser("render"); r.add_argument("input")
    r.add_argument("--outdir", default="previews")
    r.add_argument("--scale", type=int, default=4)
    r.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    r.set_defaults(func=_cmd_render)

    i = sub.add_parser("info"); i.add_argument("input")
    i.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    i.set_defaults(func=_cmd_info)

    f = sub.add_parser("flatten"); f.add_argument("input")
    f.add_argument("-o", "--output", default=None)
    f.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    f.set_defaults(func=_cmd_flatten)

    po = sub.add_parser("pose"); po.add_argument("input")
    po.add_argument("--pose", choices=sorted(POSES), default="natural")
    po.add_argument("--yaw", type=float, default=45.0)
    po.add_argument("--pitch", type=float, default=25.0)
    po.add_argument("--scale", type=int, default=8)
    po.add_argument("-o", "--output", default=None)
    po.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    po.set_defaults(func=_cmd_pose)

    v = sub.add_parser("validate"); v.add_argument("input")
    v.set_defaults(func=_cmd_validate)

    pal = sub.add_parser("palette")
    pal.add_argument("--category", choices=("skin_tones", "hair", "clothing", "energy"),
                      default=None)
    pal.set_defaults(func=_cmd_palette)

    hm = sub.add_parser("harmonize",
                        help="recolor a texture into another's color family")
    hm.add_argument("input", help="texture to recolor, e.g. a skin")
    hm.add_argument("--reference", required=True,
                    help="texture to match, e.g. a cape or logo")
    hm.add_argument("-o", "--output", default=None,
                    help="default: <input>_matched.png")
    hm.add_argument("--mode", choices=HARMONIZE_MODES, default="retheme",
                    help="retheme keeps the shading ramp, palette adopts the "
                         "reference palette outright (default: retheme)")
    hm.add_argument("--strength", type=float, default=1.0,
                    help="0 = unchanged, 1 = fully matched (default: 1.0)")
    hm.add_argument("--parts", default=None,
                    help="comma list, e.g. body,left_leg")
    hm.add_argument("--layers", default=None, help="base,overlay")
    hm.add_argument("--faces", default=None,
                    help="front,back,left,right,top,bottom")
    hm.add_argument("--model", choices=("steve", "alex", "auto"), default="auto")
    hm.set_defaults(func=_cmd_harmonize)

    tx = sub.add_parser("texture",
                        help="generate a block sheet or an item icon "
                             "(needs the gamedata extra)")
    tx.add_argument("name", help="block or item name, e.g. sculk_sensor")
    tx.add_argument("--color", required=True,
                    help="base color (R,G,B or #RRGGBB)")
    tx.add_argument("-o", "--outdir", default="textures")
    tx.add_argument("--scale", type=int, default=1,
                    help="write Nx nearest-neighbour upscales")
    tx.add_argument("--style", default="combined",
                    choices=sorted(set(SHADING_STYLES) | set(STYLE_PROFILES)),
                    help="shading style or style profile")
    tx.add_argument("--material", choices=sorted(MATERIALS), default=None,
                    help="material recipe, overrides --style")
    tx.add_argument("--shape", choices=sorted(T.ICON_ART), default="gem",
                    help="item silhouette archetype")
    tx.add_argument("--noise", type=int, default=0,
                    help="fabric grain variance (0 = none)")
    tx.add_argument("--seed", type=int, default=0)
    tx.add_argument("--glow", action=argparse.BooleanOptionalAction,
                    default=None,
                    help="emissive lift (default: the block's emitLight)")
    tx.add_argument("--glow-strength", type=float, default=0.35)
    tx.add_argument("--tint-ready", action=argparse.BooleanOptionalAction,
                    default=None,
                    help="greyscale, for a runtime biome tint "
                         "(default: the block's tint group)")
    tx.add_argument("--alpha", type=int, default=255)
    tx.add_argument("--version", default=None, help="e.g. 1.21.6 (default: latest)")
    tx.add_argument("--edition", choices=G.EDITIONS, default=G.PC)
    tx.set_defaults(func=_cmd_texture)

    gd = sub.add_parser("gamedata",
                        help="vanilla Minecraft data (needs the gamedata extra)")
    gd.add_argument("what", nargs="?", default="overview",
                    choices=("overview", "versions", "styles", "style", "search",
                             "formats", "blocks", "items", "entities", "particles",
                             "biomes", "tints", "palette", "theme", "spec"),
                    help="what to inspect")
    gd.add_argument("term", nargs="?", default=None,
                    help="style name, search phrase, or tint group")
    gd.add_argument("--version", default=None, help="e.g. 1.21.6 (default: latest)")
    gd.add_argument("--edition", choices=G.EDITIONS, default=G.PC)
    gd.add_argument("--min", type=int, default=4, dest="min_members",
                    help="minimum members for a style family")
    gd.add_argument("--limit", type=int, default=40)
    gd.set_defaults(func=_cmd_gamedata)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
