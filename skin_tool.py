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
    python skin_tool.py render skin.png --outdir previews
    python skin_tool.py info skin.png
    python skin_tool.py flatten skin.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skinlib.model import Skin, PARTS, LAYERS, FACES, parse_color, create, load
from skinlib.shading import apply_shading
from skinlib.patterns import apply_pattern, PATTERNS
from skinlib.sampling import sample_palette
from skinlib.render import save_previews, render_3d
from skinlib.templates import build_template, TEMPLATES
from skinlib.palette import all_palettes
from skinlib.validate import validate_report
from skinlib.poses import POSES
from skinlib.decoration import apply_3d_decoration


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
                  noise=a.noise, noise_var=a.noise_var)
    s.save(out)
    print(f"shaded {a.part}/{a.layer} ({a.style}) -> {out}")


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
    pa.add_argument("--model", choices=("steve", "alex"), default="steve")
    pa.set_defaults(func=_cmd_paint)

    sh = sub.add_parser("shading"); sh.add_argument("input")
    sh.add_argument("--part", required=True, choices=PARTS)
    sh.add_argument("--color", required=True)
    sh.add_argument("--layer", choices=LAYERS, default="base")
    sh.add_argument("--style", choices=("flat", "vertical", "cylindrical", "combined", "artistic"), default="combined")
    sh.add_argument("--noise", action="store_true")
    sh.add_argument("--noise-var", type=int, default=6)
    sh.add_argument("-o", "--output", default=None)
    sh.add_argument("--model", choices=("steve", "alex"), default="steve")
    sh.set_defaults(func=_cmd_shading)

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
    pt.add_argument("--model", choices=("steve", "alex"), default="steve")
    pt.set_defaults(func=_cmd_pattern)

    t = sub.add_parser("template"); t.add_argument("name")
    t.add_argument("-o", "--output", default="skin.png")
    t.set_defaults(func=_cmd_template)

    dec = sub.add_parser("decorate"); dec.add_argument("input")
    dec.add_argument("--hat", default=None, help="hat color (R,G,B)")
    dec.add_argument("--jacket", default=None, help="jacket/zipper color (R,G,B)")
    dec.add_argument("--pants", default=None, help="pants hem color (R,G,B)")
    dec.add_argument("-o", "--output", default=None)
    dec.add_argument("--model", choices=("steve", "alex"), default="steve")
    dec.set_defaults(func=_cmd_decorate)

    sm = sub.add_parser("sample"); sm.add_argument("input")
    sm.add_argument("--colors", type=int, default=6)
    sm.set_defaults(func=_cmd_sample)

    r = sub.add_parser("render"); r.add_argument("input")
    r.add_argument("--outdir", default="previews")
    r.add_argument("--scale", type=int, default=4)
    r.add_argument("--model", choices=("steve", "alex"), default="steve")
    r.set_defaults(func=_cmd_render)

    i = sub.add_parser("info"); i.add_argument("input")
    i.add_argument("--model", choices=("steve", "alex"), default="steve")
    i.set_defaults(func=_cmd_info)

    f = sub.add_parser("flatten"); f.add_argument("input")
    f.add_argument("-o", "--output", default=None)
    f.add_argument("--model", choices=("steve", "alex"), default="steve")
    f.set_defaults(func=_cmd_flatten)

    po = sub.add_parser("pose"); po.add_argument("input")
    po.add_argument("--pose", choices=sorted(POSES), default="natural")
    po.add_argument("--yaw", type=float, default=45.0)
    po.add_argument("--pitch", type=float, default=25.0)
    po.add_argument("--scale", type=int, default=8)
    po.add_argument("-o", "--output", default=None)
    po.add_argument("--model", choices=("steve", "alex"), default="steve")
    po.set_defaults(func=_cmd_pose)

    v = sub.add_parser("validate"); v.add_argument("input")
    v.set_defaults(func=_cmd_validate)

    pal = sub.add_parser("palette")
    pal.add_argument("--category", choices=("skin_tones", "hair", "clothing", "energy"),
                      default=None)
    pal.set_defaults(func=_cmd_palette)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
