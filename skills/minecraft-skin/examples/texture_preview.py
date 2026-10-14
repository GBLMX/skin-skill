#!/usr/bin/env python3
"""Preview generated block textures: a contact sheet + an isometric cube.

Both outputs are plain Pillow -- no renderer, no browser, no extra dependency:

    python texture_preview.py --color 42,77,74                 # a block sheet
    python texture_preview.py --name sculk_sensor --color 42,77,74
    python texture_preview.py --input out/*.png -o previews    # arbitrary PNGs

The cube is the useful one for judging the vanilla face convention: a block
sheet only reads as 3D once top/side/bottom sit next to each other with the
top brightest and the bottom darkest.  See references/texture_preview.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance

# Vanilla cube lighting between the two visible sides (the sheet already
# carries top>side>bottom; this is the extra side-vs-side contrast).
WEST_SHADE = 0.72


def contact_sheet(paths, cols: int = 8, cell: int = 64, pad: int = 8,
                  bg=(24, 24, 28, 255)):
    """Tile a batch of textures, nearest-neighbour upscaled, in name order."""
    paths = sorted(Path(p) for p in paths)
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new(
        "RGBA", (cols * (cell + pad) + pad, rows * (cell + pad) + pad), bg)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGBA")
        img = img.resize((cell, cell), Image.NEAREST)
        sheet.alpha_composite(
            img, (pad + (i % cols) * (cell + pad),
                  pad + (i // cols) * (cell + pad)))
    return sheet, [p.name for p in paths]


def _paste_quad(canvas, tex, tl, tr, bl, br):
    """Affine-map a rectangular texture onto a screen parallelogram.

    Orthographic projection keeps a face planar, so one affine transform maps
    it exactly.  ``tl/tr/bl/br`` are the texture's corners in screen space.
    """
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = tl, tr, bl, br
    w, h = tex.size
    den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(den) < 1e-9:
        return
    a, b = w * (y2 - y0) / den, -w * (x2 - x0) / den
    d, e = -h * (y1 - y0) / den, h * (x1 - x0) / den
    c, f = -a * x0 - b * y0, -d * x0 - e * y0
    minx, miny = int(min(x0, x1, x2, x3)), int(min(y0, y1, y2, y3))
    maxx, maxy = int(max(x0, x1, x2, x3)) + 1, int(max(y0, y1, y2, y3)) + 1
    mapped = tex.transform(
        (maxx - minx, maxy - miny), Image.AFFINE,
        (a, b, a * minx + b * miny + c, d, e, d * minx + e * miny + f),
        Image.NEAREST)
    canvas.alpha_composite(mapped, (minx, miny))


def iso_cube(tex, scale: int = 10, margin: int = 8):
    """Compose a block sheet's top/side faces into an isometric cube.

    Returns ``None`` when the canvas has no top/side faces to show.
    """
    if "top" not in tex.faces or "side" not in tex.faces:
        return None
    a = tex.width * scale
    top = tex.face_image("all", "base", "top").resize((a, a), Image.NEAREST)
    side = tex.face_image("all", "base", "side").resize((a, a), Image.NEAREST)
    west = ImageEnhance.Brightness(side).enhance(WEST_SHADE)
    canvas = Image.new("RGBA", (2 * a + 2 * margin, 2 * a + a // 2 + 2 * margin),
                       (0, 0, 0, 0))
    ox, oy = margin, margin
    # top rhombus: texture TL -> north, TR -> east, BL -> west, BR -> south
    _paste_quad(canvas, top,
                (ox + a, oy), (ox + 2 * a, oy + a // 2),
                (ox, oy + a // 2), (ox + a, oy + a))
    # west face
    _paste_quad(canvas, west,
                (ox, oy + a // 2), (ox + a, oy + a),
                (ox, oy + a // 2 + a), (ox + a, oy + a + a))
    # east face (full brightness)
    _paste_quad(canvas, side,
                (ox + a, oy + a), (ox + 2 * a, oy + a // 2),
                (ox + a, oy + a + a), (ox + 2 * a, oy + a // 2 + a))
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--color", default="42,77,74",
                    help="base color for a generated block sheet (R,G,B)")
    ap.add_argument("--name", default=None,
                    help="registry name, e.g. sculk_sensor (needs the gamedata extra)")
    ap.add_argument("--input", nargs="*", default=None,
                    help="PNG files to tile instead of generating a sheet")
    ap.add_argument("-o", "--outdir", default="previews")
    ap.add_argument("--scale", type=int, default=10, help="cube upscale")
    a = ap.parse_args(argv)

    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    from skinlib import block, generate, parse_color

    color = parse_color(a.color)
    if a.input:
        sheet, names = contact_sheet(a.input)
        sheet.save(out / "contact.png")
        print(f"contact sheet ({len(names)}): {', '.join(names[:6])}"
              f"{' ...' if len(names) > 6 else ''} -> {out / 'contact.png'}")
        return

    tex = (generate(a.name, color) if a.name else block(color, noise=4))
    faces = tex.save_faces(out, a.name or "block")
    for path in faces:
        print(f"face  -> {path}")

    sheet, _ = contact_sheet(faces)
    sheet.save(out / "contact.png")
    print(f"contact -> {out / 'contact.png'}")

    cube = iso_cube(tex, scale=a.scale)
    if cube is None:
        print("cube  -> skipped (needs top and side faces)")
        return
    cube.save(out / "cube.png")
    alpha = cube.getchannel("A")
    painted = cube.width * cube.height - alpha.histogram()[0]
    print(f"cube  -> {out / 'cube.png'}  "
          f"({painted} px painted, 3 faces = {3 * (tex.width * a.scale) ** 2})")


if __name__ == "__main__":
    main()
