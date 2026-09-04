"""Core data model: UV layouts and the Skin object.

This module contains only data (no rendering logic) to keep responsibilities
clean. Colors, shading, patterns, sampling, and rendering are separate modules.

Layouts are pure data — Steve (4px arms) and Alex (3px slim arms). Each is a
mapping from (part, layer, face) to a (x, y, w, h) box in a 64x64 texture.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Literal, Tuple

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Part = Literal["head", "body", "right_arm", "left_arm", "right_leg", "left_leg"]
Layer = Literal["base", "overlay"]
Face = Literal["front", "right", "top", "bottom", "back", "left"]
Color = Tuple[int, int, int, int]  # RGBA

PARTS: Tuple[Part, ...] = (
    "head", "body", "right_arm", "left_arm", "right_leg", "left_leg",
)
LAYERS: Tuple[Layer, ...] = ("base", "overlay")
FACES: Tuple[Face, ...] = ("front", "right", "top", "bottom", "back", "left")


@dataclass(frozen=True)
class Box:
    """A texture region (x, y, width, height) in UV space."""
    x: int
    y: int
    w: int
    h: int

    @property
    def xyxy(self) -> Tuple[int, int, int, int]:
        """Return (x0, y0, x1, y1) for Pillow rectangle."""
        return (self.x, self.y, self.x + self.w, self.y + self.h)


# ---------------------------------------------------------------------------
# Layouts
# ---------------------------------------------------------------------------
SteveLayout: Dict[str, Dict[str, Dict[str, Box]]] = {
    "head": {
        "base": {
            "front": Box(8, 8, 8, 8), "right": Box(0, 8, 8, 8),
            "top": Box(8, 0, 8, 8), "bottom": Box(16, 0, 8, 8),
            "back": Box(24, 8, 8, 8), "left": Box(16, 8, 8, 8),
        },
        "overlay": {
            "front": Box(40, 8, 8, 8), "right": Box(32, 8, 8, 8),
            "top": Box(40, 0, 8, 8), "bottom": Box(48, 0, 8, 8),
            "back": Box(56, 8, 8, 8), "left": Box(48, 8, 8, 8),
        },
    },
    "body": {
        "base": {
            "front": Box(20, 20, 8, 12), "right": Box(16, 20, 4, 12),
            "top": Box(20, 16, 8, 4), "bottom": Box(28, 16, 8, 4),
            "back": Box(32, 20, 8, 12), "left": Box(28, 20, 4, 12),
        },
        "overlay": {
            "front": Box(20, 36, 8, 12), "right": Box(16, 36, 4, 12),
            "top": Box(20, 32, 8, 4), "bottom": Box(28, 32, 8, 4),
            "back": Box(32, 36, 8, 12), "left": Box(28, 36, 4, 12),
        },
    },
    "right_arm": {
        "base": {
            "front": Box(44, 20, 4, 12), "right": Box(40, 20, 4, 12),
            "top": Box(44, 16, 4, 4), "bottom": Box(48, 16, 4, 4),
            "back": Box(52, 20, 4, 12), "left": Box(48, 20, 4, 12),
        },
        "overlay": {
            "front": Box(44, 36, 4, 12), "right": Box(40, 36, 4, 12),
            "top": Box(44, 32, 4, 4), "bottom": Box(48, 32, 4, 4),
            "back": Box(52, 36, 4, 12), "left": Box(48, 36, 4, 12),
        },
    },
    "left_arm": {
        "base": {
            "front": Box(36, 52, 4, 12), "right": Box(32, 52, 4, 12),
            "top": Box(36, 48, 4, 4), "bottom": Box(40, 48, 4, 4),
            "back": Box(44, 52, 4, 12), "left": Box(40, 52, 4, 12),
        },
        "overlay": {
            "front": Box(52, 52, 4, 12), "right": Box(48, 52, 4, 12),
            "top": Box(52, 48, 4, 4), "bottom": Box(56, 48, 4, 4),
            "back": Box(60, 52, 4, 12), "left": Box(56, 52, 4, 12),
        },
    },
    "right_leg": {
        "base": {
            "front": Box(4, 20, 4, 12), "right": Box(0, 20, 4, 12),
            "top": Box(4, 16, 4, 4), "bottom": Box(8, 16, 4, 4),
            "back": Box(12, 20, 4, 12), "left": Box(8, 20, 4, 12),
        },
        "overlay": {
            "front": Box(4, 36, 4, 12), "right": Box(0, 36, 4, 12),
            "top": Box(4, 32, 4, 4), "bottom": Box(8, 32, 4, 4),
            "back": Box(12, 36, 4, 12), "left": Box(8, 36, 4, 12),
        },
    },
    "left_leg": {
        "base": {
            "front": Box(20, 52, 4, 12), "right": Box(16, 52, 4, 12),
            "top": Box(20, 48, 4, 4), "bottom": Box(24, 48, 4, 4),
            "back": Box(28, 52, 4, 12), "left": Box(24, 52, 4, 12),
        },
        "overlay": {
            "front": Box(4, 52, 4, 12), "right": Box(0, 52, 4, 12),
            "top": Box(4, 48, 4, 4), "bottom": Box(8, 48, 4, 4),
            "back": Box(12, 52, 4, 12), "left": Box(8, 52, 4, 12),
        },
    },
}


def _slim_arms() -> Dict[str, Dict[str, Dict[str, Box]]]:
    """Alex slim arms: 3px wide instead of 4."""
    return {
        "right_arm": {
            "base": {
                "front": Box(44, 20, 3, 12), "right": Box(40, 20, 3, 12),
                "top": Box(44, 16, 3, 4), "bottom": Box(47, 16, 3, 4),
                "back": Box(51, 20, 3, 12), "left": Box(47, 20, 3, 12),
            },
            "overlay": {
                "front": Box(44, 36, 3, 12), "right": Box(40, 36, 3, 12),
                "top": Box(44, 32, 3, 4), "bottom": Box(47, 32, 3, 4),
                "back": Box(51, 36, 3, 12), "left": Box(47, 36, 3, 12),
            },
        },
        "left_arm": {
            "base": {
                "front": Box(36, 52, 3, 12), "right": Box(32, 52, 3, 12),
                "top": Box(36, 48, 3, 4), "bottom": Box(39, 48, 3, 4),
                "back": Box(43, 52, 3, 12), "left": Box(39, 52, 3, 12),
            },
            "overlay": {
                "front": Box(52, 52, 3, 12), "right": Box(48, 52, 3, 12),
                "top": Box(52, 48, 3, 4), "bottom": Box(55, 48, 3, 4),
                "back": Box(59, 52, 3, 12), "left": Box(55, 52, 3, 12),
            },
        },
    }


def make_layout(model: str = "steve") -> Dict[str, Dict[str, Dict[str, Box]]]:
    """Return a full layout dict for the given model ('steve' or 'alex')."""
    import copy
    layout = copy.deepcopy(SteveLayout)
    if model == "alex":
        layout.update(_slim_arms())
    return layout


def legacy_to_modern(img: Image.Image) -> Image.Image:
    """Convert a legacy 64x32 skin to the modern 64x64 layout.

    Legacy skins store a single (right) arm and leg texture, which the game
    mirrors onto both sides, and have no overlay layer. The head/body base
    faces already share coordinates with the modern layout, so the 64x32
    sheet is pasted into the top half, and the right arm/leg blocks are
    copied into the left arm/leg base regions.
    """
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(img, (0, 0))                              # head, body, right arm/leg
    out.paste(img.crop((40, 16, 56, 32)), (32, 48))     # right arm -> left arm
    out.paste(img.crop((0, 16, 16, 32)), (16, 48))      # right leg -> left leg
    return out


def detect_model(img: Image.Image) -> str:
    """Detect 'steve' (4px arms) vs 'alex' (3px slim arms) heuristically.

    Slim (Alex) skins leave a 1px transparent column in the right-arm band —
    the gap between the left and back faces — while Steve skins fill all 16
    columns. Sample column x=50 across the vertical arm faces.
    """
    opaque = 0
    for y in (22, 24, 26, 28, 30):
        if img.getpixel((50, y))[3] > 16:
            opaque += 1
    return "steve" if opaque >= 3 else "alex"


def strip_matte(img: Image.Image) -> Image.Image:
    """Remove a solid-color alpha matte, per the Minecraft skin convention.

    Mojang serves many skins with a *matte*: the exact RGBA of the top-left
    pixel marks "transparent" instead of a real alpha channel (see
    https://github.com/minotar/skin-spec). If the top-left pixel is opaque,
    every pixel equal to it becomes fully transparent. No-op for skins that
    already use a real alpha channel (top-left alpha == 0).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    key = img.getpixel((0, 0))
    if key[3] == 0:
        return img
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] == key:
                px[x, y] = (key[0], key[1], key[2], 0)
    return img


# ---------------------------------------------------------------------------
# Color parsing
# ---------------------------------------------------------------------------
def parse_color(s: str) -> Color:
    """Parse 'R,G,B', 'R,G,B,A', '#RRGGBB', or '#RRGGBBAA' into RGBA."""
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        if len(h) == 8:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
        raise ValueError(f"bad hex color {s!r}")
    parts = [p.strip() for p in s.split(",")]
    if len(parts) == 3:
        parts.append("255")
    if len(parts) != 4:
        raise ValueError(f"color must be R,G,B[,A] or hex: {s!r}")
    return tuple(int(p) for p in parts)


# ---------------------------------------------------------------------------
# Skin object
# ---------------------------------------------------------------------------
class Skin:
    """A Minecraft skin. Provides pixel access and high-level painting.

    All mutation happens through methods here or the functional modules
    (shading/patterns). Rendering and sampling live elsewhere.
    """

    def __init__(self, size: int = 64, model: str = "steve",
                 transparent: bool = True):
        if size not in (64, 128):
            raise ValueError("size must be 64 or 128")
        self.size = size
        self.model = model
        self.scale = size // 64
        self.layout = make_layout(model)
        bg = (0, 0, 0, 0) if transparent else (255, 255, 255, 255)
        self.img = Image.new("RGBA", (size, size), bg)
        self.draw = ImageDraw.Draw(self.img)

    # -- region access ------------------------------------------------------
    def box(self, part: Part, layer: Layer, face: Face) -> Box:
        """Return the (scaled) Box for a part/layer/face."""
        b = self.layout[part][layer][face]
        return Box(b.x * self.scale, b.y * self.scale,
                   b.w * self.scale, b.h * self.scale)

    def region(self, part: Part, layer: Layer, face: Face) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) for a part/layer/face (scaled)."""
        b = self.box(part, layer, face)
        return (b.x, b.y, b.w, b.h)

    # -- pixel access -------------------------------------------------------
    def pixel(self, part: Part, layer: Layer, face: Face, u: int, v: int, color):
        """Paint one logical pixel (64px grid) as a scale-aware block.

        u/v are logical coordinates in the 64px skin layout. On 128px skins
        each logical pixel expands to a ``scale x scale`` block, so callers
        can keep 64px coordinates regardless of resolution.
        """
        x, y, w, h = self.region(part, layer, face)
        lw, lh = w // self.scale, h // self.scale
        if not (0 <= u < lw and 0 <= v < lh):
            raise ValueError(f"({u},{v}) outside {part}/{layer}/{face}")
        x0, y0 = x + u * self.scale, y + v * self.scale
        for du in range(self.scale):
            for dv in range(self.scale):
                self.img.putpixel((x0 + du, y0 + dv), color)

    def get_pixel(self, part: Part, layer: Layer, face: Face, u: int, v: int) -> Color:
        """Return the color of a logical pixel (top-left of its block)."""
        x, y, w, h = self.region(part, layer, face)
        return self.img.getpixel((x + u * self.scale, y + v * self.scale))

    def dump(self, part: Part, face: Face = "front",
             layers: Tuple[Layer, ...] = ("base", "overlay")) -> None:
        """逐 v 打印 part/face 的 base/overlay 像素，调试层次冲突（techniques §15）。

        透明像素显示为 ``·``，不透明显示 R 通道值（3 位对齐），base/overlay 两行
        并排对比，一眼看出谁遮了谁。
        """
        b = self.box(part, "base", face)
        lw, lh = b.w // self.scale, b.h // self.scale
        u = lw // 2
        for layer in layers:
            cells = []
            for v in range(lh):
                c = self.get_pixel(part, layer, face, u, v)
                cells.append(" · " if c[3] == 0 else f"{c[0]:3d}")
            print(f"{part}/{layer}/{face}: " + " ".join(cells))

    # -- face / part painting ----------------------------------------------
    def paint_face(self, part: Part, layer: Layer, face: Face, color):
        x, y, w, h = self.region(part, layer, face)
        # PIL rectangle endpoints are inclusive, so subtract 1 to fill exactly w x h.
        self.draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)

    def paint_part(self, part: Part, color, layer: Layer = "base"):
        for face in FACES:
            self.paint_face(part, layer, face, color)

    def fill_parts(self, color, parts=PARTS, layer: Layer = "base"):
        for p in parts:
            self.paint_part(p, color, layer)

    # -- face image I/O -----------------------------------------------------
    def face_image(self, part: Part, layer: Layer, face: Face) -> Image.Image:
        x, y, w, h = self.region(part, layer, face)
        return self.img.crop((x, y, x + w, y + h))

    def paste_face(self, part: Part, layer: Layer, face: Face, image: Image.Image):
        x, y, w, h = self.region(part, layer, face)
        if image.size != (w, h):
            image = image.resize((w, h), Image.NEAREST)
        self.img.paste(image, (x, y), image if image.mode == "RGBA" else None)

    # -- layer operations ---------------------------------------------------
    def layer_image(self, layer: Layer) -> Image.Image:
        """Extract one layer (other areas transparent)."""
        out = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        for part in PARTS:
            for face in FACES:
                x, y, w, h = self.region(part, layer, face)
                out.paste(self.img.crop((x, y, x + w, y + h)), (x, y))
        return out

    def flatten(self) -> "Skin":
        """Bake overlay onto base into a new single-layer skin."""
        flat = Skin(size=self.size, model=self.model)
        base = self.layer_image("base")
        over = self.layer_image("overlay")
        flat.img = Image.alpha_composite(base, over)
        flat.draw = ImageDraw.Draw(flat.img)
        # clear overlay in flat result
        for part in PARTS:
            for face in FACES:
                flat.paint_face(part, "overlay", face, (0, 0, 0, 0))
        return flat

    # -- IO -----------------------------------------------------------------
    def save(self, path: str) -> Path:
        self.img.save(path)
        return Path(path)

    @classmethod
    def load(cls, path: str, model: str = "auto") -> "Skin":
        img = Image.open(path).convert("RGBA")
        if img.size not in ((64, 64), (128, 128), (64, 32)):
            raise ValueError("skin must be 64x64, 128x128, or 64x32")
        img = strip_matte(img)
        if img.size == (64, 32):
            img = legacy_to_modern(img)
        if model == "auto":
            model = detect_model(img)
        s = cls(size=img.size[0], model=model)
        s.img = img
        s.draw = ImageDraw.Draw(img)
        return s


# Convenience aliases
def create(size: int = 64, model: str = "steve") -> Skin:
    return Skin(size=size, model=model)


def load(path: str, model: str = "auto") -> Skin:
    return Skin.load(path, model)
