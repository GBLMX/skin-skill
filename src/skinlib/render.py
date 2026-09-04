"""Rendering: flat, isometric, and orthographic 3D previews.

Uses a proper orthographic projection of the actual body-part cubes, so the
previews reflect the real 3D structure (head/body/arms/legs) rather than a
flat approximation.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image

from .model import Skin, Box, PARTS
from .poses import get_pose, PartPose


# ---------------------------------------------------------------------------
# Body-part dimensions in voxel units (Steve proportions).
# (width_x, height_y, depth_z)
# ---------------------------------------------------------------------------
PART_DIMS: Dict[str, Tuple[int, int, int]] = {
    "head": (8, 8, 8),
    "body": (8, 12, 4),
    "right_arm": (4, 12, 4),
    "left_arm": (4, 12, 4),
    "right_leg": (4, 12, 4),
    "left_leg": (4, 12, 4),
}


def _part_dims(model: str) -> Dict[str, Tuple[int, int, int]]:
    """Return body-part dimensions for the model (Alex arms are 3px slim)."""
    dims = dict(PART_DIMS)
    if model == "alex":
        dims["right_arm"] = (3, 12, 4)
        dims["left_arm"] = (3, 12, 4)
    return dims

# Part positions (center, in voxel units) relative to body center at (0,0,0).
PART_ORIGIN: Dict[str, Tuple[int, int, int]] = {
    "head": (0, 28, 0),
    "body": (0, 18, 0),
    "right_arm": (-6, 18, 0),
    "left_arm": (6, 18, 0),
    "right_leg": (-2, 6, 0),
    "left_leg": (2, 6, 0),
}


def _composite_face(skin: Skin, part, face):
    base = skin.face_image(part, "base", face)
    over = skin.face_image(part, "overlay", face)
    return Image.alpha_composite(base, over)


def render_flat(skin: Skin, scale: int = 4) -> Image.Image:
    """Raw texture sheet upscaled (nearest-neighbor)."""
    return skin.img.resize((skin.size * scale, skin.size * scale), Image.NEAREST)


def render_isometric(skin: Skin, view: str = "front",
                     scale: int = 4, size: Tuple[int, int] = (320, 400)) -> Image.Image:
    """Front or back body layout using the actual face textures."""
    face = "front" if view == "front" else "back"
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    cx, cy = size[0] // 2, size[1] // 2
    s = scale * 2

    layout = [
        ("head", (0, -30)),
        ("body", (0, -2)),
        ("right_arm", (-13, -2)),
        ("left_arm", (13, -2)),
        ("right_leg", (-5, 26)),
        ("left_leg", (5, 26)),
    ]
    dims = _part_dims(skin.model)
    for part, (dx, dy) in layout:
        tex = _composite_face(skin, part, face)
        w, h = dims[part][0], dims[part][1]
        tex = tex.resize((w * s, h * s), Image.NEAREST)
        px = cx + int(dx * scale) - tex.width // 2
        py = cy + int(dy * scale) - tex.height // 2
        img.paste(tex, (px, py), tex)
    return img


def render_3d(skin: Skin, yaw: float = 45.0, pitch: float = 25.0,
              scale: int = 8, size: Tuple[int, int] = (400, 500),
              pose: str = "natural") -> Image.Image:
    """Orthographic 3D render of all body-part cubes.

    yaw/pitch in degrees, pose in ('natural','walking','sitting','crouching',
    'jumping','aiming'). Projects each voxel cube's visible faces using the
    real face textures.
    """
    part_pose = get_pose(pose)

    # Rotation matrices
    def rot(x, y, z):
        # yaw around Y, then pitch around X
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cx, sx = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        # yaw
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        # pitch
        y1 = y * cx - z1 * sx
        z2 = y * sx + z1 * cx
        return x1, y1, z2

    img = Image.new("RGBA", size, (0, 0, 0, 0))
    cx, cy = size[0] // 2, size[1] // 2

    # Cube corners are generated in the order dx, dy, dz (each -/+ half),
    # so corner index = dx*4 + dy*2 + dz. Map each face to the corner indices
    # for its [top-left, top-right, bottom-right, bottom-left] texture corners.
    face_map = {
        "front":  [2, 3, 1, 0],
        "back":   [6, 7, 5, 4],
        "right":  [2, 6, 4, 0],
        "left":   [3, 7, 5, 1],
        "top":    [2, 6, 7, 3],
        "bottom": [0, 4, 5, 1],
    }

    order = ["right_leg", "left_leg", "right_arm", "left_arm", "body", "head"]
    quads = []  # (depth, texture, [4 screen points])
    dims = _part_dims(skin.model)
    for part in order:
        w, h, d = dims[part]
        ox, oy, oz = PART_ORIGIN[part]
        pp = part_pose.get(part, PartPose())

        def part_rot(dx, dy, dz):
            # local part rotation (rx, ry, rz) around part origin, then
            # translate by part pose offset, then global view rotation
            x, y, z = dx, dy, dz
            if pp.rx:
                a = math.radians(pp.rx)
                y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
            if pp.ry:
                a = math.radians(pp.ry)
                x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
            if pp.rz:
                a = math.radians(pp.rz)
                x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            return x + pp.dx, y + pp.dy, z + pp.dz

        # Java hat layer: overlay floats outside base (head +0.5, body/limbs +0.25)
        # voxel units. Render base first, then the inflated overlay cube so the
        # preview shows the real second-layer depth the game renders.
        inflate = 0.5 if part == "head" else 0.25
        for layer, f in (("base", 0.0), ("overlay", inflate)):
            ww, hh, dd = w + 2 * f, h + 2 * f, d + 2 * f
            # corners relative to center
            corners = []
            for dx in (-ww / 2, ww / 2):
                for dy in (-hh / 2, hh / 2):
                    for dz in (-dd / 2, dd / 2):
                        lx, ly, lz = part_rot(dx, dy, dz)
                        X, Y, Z = rot(ox + lx, oy + ly, oz + lz)
                        corners.append((cx + X * scale, cy - Y * scale, Z))

            for face, idxs in face_map.items():
                tex = skin.face_image(part, layer, face)
                if layer == "overlay" and tex.getbbox() is None:
                    continue  # skip fully-transparent overlay faces
                pts = [corners[i] for i in idxs]
                # backface culling via view-space face normal (z <= 0 => facing away)
                p0, p1, p2 = pts[0], pts[1], pts[2]
                u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                n = (u[1] * v[2] - u[2] * v[1],
                     u[2] * v[0] - u[0] * v[2],
                     u[0] * v[1] - u[1] * v[0])
                if n[2] <= 0:
                    continue
                depth = sum(p[2] for p in pts) / 4.0
                quads.append((depth, tex, pts))

    # Painter's algorithm: draw farthest faces first.
    quads.sort(key=lambda q: q[0])
    for _, tex, pts in quads:
        _paste_affine(img, tex, pts[0], pts[1], pts[3], pts[2])

    return img


def _paste_affine(img: Image.Image, tex: Image.Image,
                  p_tl, p_tr, p_bl, p_br):
    """Affine-map a rectangular texture onto a projected parallelogram.

    p_tl, p_tr, p_bl, p_br are (x, y, z) screen points for the texture's
    top-left, top-right, bottom-left and bottom-right corners. Orthographic
    projection keeps a face planar, so a single affine transform maps the
    texture exactly (no bounding-box distortion).
    """
    x0, y0 = p_tl[0], p_tl[1]
    x1, y1 = p_tr[0], p_tr[1]
    x2, y2 = p_bl[0], p_bl[1]
    x3, y3 = p_br[0], p_br[1]
    w, h = tex.size

    denom = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(denom) < 1e-9:
        return

    # Inverse affine (screen -> texture): u = a*x + b*y + c, v = d*x + e*y + f
    a = w * (y2 - y0) / denom
    b = -w * (x2 - x0) / denom
    c = -a * x0 - b * y0
    d = -h * (y1 - y0) / denom
    e = h * (x1 - x0) / denom
    f = -d * x0 - e * y0

    minx = math.floor(min(x0, x1, x2, x3))
    maxx = math.ceil(max(x0, x1, x2, x3))
    miny = math.floor(min(y0, y1, y2, y3))
    maxy = math.ceil(max(y0, y1, y2, y3))
    out_w, out_h = maxx - minx, maxy - miny
    if out_w <= 0 or out_h <= 0:
        return

    A, B, C = a, b, a * minx + b * miny + c
    D, E, F = d, e, d * minx + e * miny + f
    mapped = tex.transform((out_w, out_h), Image.AFFINE,
                           (A, B, C, D, E, F), Image.NEAREST)
    img.paste(mapped, (minx, miny), mapped)


def save_previews(skin: Skin, outdir: str, scale: int = 4):
    """Generate flat, isometric front/back, and 3D previews."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    render_flat(skin, scale).save(out / "flat.png")
    render_isometric(skin, "front", scale).save(out / "iso_front.png")
    render_isometric(skin, "back", scale).save(out / "iso_back.png")
    render_3d(skin, scale=6).save(out / "render_3d.png")
    return out
